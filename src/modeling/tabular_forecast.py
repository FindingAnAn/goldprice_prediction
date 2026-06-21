"""Leakage-safe direct multi-horizon forecasting with tabular ML models."""

from __future__ import annotations

from dataclasses import dataclass
import time

import numpy as np
import pandas as pd
from sklearn.compose import TransformedTargetRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

from config.settings import (
    DEEP_FORECAST_HORIZONS,
    OPEN_FORECAST_HORIZON,
    OPEN_FORECAST_RANDOM_SEED,
    TABULAR_FORECAST_BASE_FEATURES,
    TABULAR_FORECAST_ENSEMBLES,
    TABULAR_FORECAST_LAGS,
    TABULAR_FORECAST_MODELS,
    TABULAR_FORECAST_TRAINING_WINDOW,
    TABULAR_FORECAST_WINDOWS,
)
from src.modeling.open_forecast import next_estimated_session_dates


@dataclass(frozen=True)
class DirectForecastModel:
    """Production estimators and their stable feature contract."""

    model_name: str
    estimators: dict[int, object]
    feature_columns: tuple[str, ...]
    training_window_sessions: int


@dataclass(frozen=True)
class DirectForecastEnsemble:
    """Fixed-weight blend of production direct models."""

    model_name: str
    component_models: tuple[str, ...]
    weights: tuple[float, ...]


@dataclass(frozen=True)
class TabularBenchmarkResult:
    """Artifacts and diagnostics from the direct tabular benchmark."""

    metrics: pd.DataFrame
    rolling_predictions: pd.DataFrame
    future_predictions: pd.DataFrame
    fitted_models: dict[str, DirectForecastModel | DirectForecastEnsemble]
    training_seconds: dict[str, float]
    feature_columns: tuple[str, ...]
    feature_importance: pd.DataFrame
    training_rows: int
    training_start_date: pd.Timestamp
    training_end_date: pd.Timestamp


def build_tabular_feature_frame(master_features: pd.DataFrame) -> pd.DataFrame:
    """Create stationary, point-in-time features from the master feature set."""

    master = master_features.sort_index().replace([np.inf, -np.inf], np.nan)
    feature_values: dict[str, pd.Series] = {}
    for column in TABULAR_FORECAST_BASE_FEATURES:
        if column in master.columns:
            feature_values[column] = pd.to_numeric(
                master[column],
                errors="coerce",
            )

    close = pd.to_numeric(master["gold_close"], errors="coerce")
    open_price = pd.to_numeric(master["gold_open"], errors="coerce")
    high = pd.to_numeric(master["gold_high"], errors="coerce")
    low = pd.to_numeric(master["gold_low"], errors="coerce")
    log_close = np.log(close.where(close > 0))
    daily_return = log_close.diff()

    feature_values["gold_overnight_gap_log"] = np.log(
        open_price.where(open_price > 0) / close.shift(1).where(close.shift(1) > 0)
    )
    feature_values["gold_intraday_return_log"] = np.log(
        close.where(close > 0) / open_price.where(open_price > 0)
    )
    feature_values["gold_range_pct"] = 100.0 * (high - low) / close
    feature_values["gold_close_location"] = (
        (close - low) / (high - low).replace(0, np.nan)
    )

    for lag in TABULAR_FORECAST_LAGS:
        feature_values[f"gold_log_return_{lag}d"] = log_close.diff(lag)
        feature_values[f"gold_daily_return_lag_{lag}"] = daily_return.shift(lag)

    for window in TABULAR_FORECAST_WINDOWS:
        rolling_return = daily_return.rolling(window, min_periods=window)
        rolling_close = close.rolling(window, min_periods=window)
        feature_values[f"gold_return_mean_{window}d"] = rolling_return.mean()
        feature_values[
            f"gold_return_volatility_{window}d"
        ] = rolling_return.std()
        feature_values[f"gold_return_min_{window}d"] = rolling_return.min()
        feature_values[f"gold_return_max_{window}d"] = rolling_return.max()
        feature_values[f"gold_trend_slope_{window}d"] = (
            log_close - log_close.shift(window - 1)
        ) / float(window - 1)
        feature_values[f"gold_price_to_mean_{window}d"] = (
            close / rolling_close.mean() - 1.0
        )
        feature_values[f"gold_drawdown_{window}d"] = (
            close / rolling_close.max() - 1.0
        )
        feature_values[f"gold_rebound_{window}d"] = (
            close / rolling_close.min() - 1.0
        )

    volume = pd.to_numeric(master.get("gold_volume"), errors="coerce")
    if volume is not None:
        log_volume = np.log1p(volume.clip(lower=0))
        for window in (21, 63, 252):
            rolling = log_volume.rolling(window, min_periods=window)
            feature_values[f"gold_volume_zscore_{window}d"] = (
                log_volume - rolling.mean()
            ) / rolling.std().replace(0, np.nan)

    # Forward-fill only: every retained value was observed on or before the
    # prediction cutoff. No backward fill or future target is allowed.
    output = pd.DataFrame(feature_values, index=master.index)
    return output.ffill().replace([np.inf, -np.inf], np.nan)


def _future_calendar_frame(
    index: pd.DatetimeIndex,
    horizon: int,
    production_date: pd.Timestamp | None = None,
) -> pd.DataFrame:
    if production_date is None:
        future_dates = pd.Series(index, index=index).shift(-horizon)
    else:
        future_dates = pd.Series(production_date, index=index)
    month = future_dates.dt.month.astype(float)
    day_of_year = future_dates.dt.dayofyear.astype(float)
    return pd.DataFrame(
        {
            "future_month_sin": np.sin(2.0 * np.pi * month / 12.0),
            "future_month_cos": np.cos(2.0 * np.pi * month / 12.0),
            "future_year_sin": np.sin(2.0 * np.pi * day_of_year / 365.25),
            "future_year_cos": np.cos(2.0 * np.pi * day_of_year / 365.25),
            "forecast_horizon": float(horizon),
        },
        index=index,
    )


def _build_estimator(model_name: str) -> object:
    if model_name == "RidgeDirect":
        regressor = Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(
                        strategy="median",
                        add_indicator=True,
                        keep_empty_features=True,
                    ),
                ),
                ("scaler", RobustScaler()),
                ("model", Ridge(alpha=20.0)),
            ]
        )
        return TransformedTargetRegressor(
            regressor=regressor,
            transformer=RobustScaler(),
        )

    if model_name == "XGBoostDirect":
        from xgboost import XGBRegressor

        return XGBRegressor(
            objective="reg:squarederror",
            n_estimators=240,
            learning_rate=0.03,
            max_depth=3,
            min_child_weight=12,
            subsample=0.80,
            colsample_bytree=0.75,
            reg_alpha=0.10,
            reg_lambda=12.0,
            tree_method="hist",
            random_state=OPEN_FORECAST_RANDOM_SEED,
            n_jobs=4,
        )

    if model_name == "LightGBMDirect":
        from lightgbm import LGBMRegressor

        return LGBMRegressor(
            objective="huber",
            n_estimators=240,
            learning_rate=0.03,
            num_leaves=15,
            min_child_samples=40,
            subsample=0.80,
            colsample_bytree=0.75,
            reg_alpha=0.10,
            reg_lambda=12.0,
            random_state=OPEN_FORECAST_RANDOM_SEED,
            deterministic=True,
            force_col_wise=True,
            verbosity=-1,
            n_jobs=4,
        )

    raise ValueError(f"Unsupported tabular model: {model_name}")


def _training_bounds(cutoff: int, horizon: int) -> tuple[int, int]:
    """Return an inclusive label-safe training range for one forecast origin."""

    training_end = cutoff - horizon
    training_start = max(
        0,
        training_end - TABULAR_FORECAST_TRAINING_WINDOW + 1,
    )
    return training_start, training_end


def _metric_rows(
    predictions: pd.DataFrame,
    model_name: str,
) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
    for horizon in DEEP_FORECAST_HORIZONS:
        subset = predictions[predictions["step"] == horizon]
        actual = subset["actual_price"].to_numpy(dtype=float)
        current = subset["current_price"].to_numpy(dtype=float)
        predicted = subset[model_name].to_numpy(dtype=float)
        rmse = float(np.sqrt(mean_squared_error(actual, predicted)))
        absolute_error = np.abs(actual - predicted)
        rows.append(
            {
                "horizon": horizon,
                "model": model_name,
                "rmse": rmse,
                "mae": float(mean_absolute_error(actual, predicted)),
                "mape": float(
                    np.mean(absolute_error / actual) * 100.0
                ),
                "smape": float(
                    np.mean(
                        2.0
                        * absolute_error
                        / (np.abs(actual) + np.abs(predicted))
                    )
                    * 100.0
                ),
                "nrmse_mean_pct": float(
                    100.0 * rmse / np.mean(np.abs(actual))
                ),
                "direction_accuracy": float(
                    np.mean(
                        np.sign(predicted - current)
                        == np.sign(actual - current)
                    )
                ),
                "windows": len(subset),
            }
        )
    return rows


def _extract_feature_importance(
    model_name: str,
    estimators: dict[int, object],
    feature_columns: tuple[str, ...],
) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
    if model_name == "RidgeDirect":
        return rows
    for horizon, estimator in estimators.items():
        values = getattr(estimator, "feature_importances_", None)
        if values is None or len(values) != len(feature_columns):
            continue
        total = float(np.sum(values))
        normalized = values / total if total > 0 else values
        rows.extend(
            {
                "model": model_name,
                "horizon": horizon,
                "feature": feature,
                "importance": float(importance),
            }
            for feature, importance in zip(feature_columns, normalized)
        )
    return rows


def benchmark_tabular_models(
    n_windows: int,
    master_features: pd.DataFrame,
) -> TabularBenchmarkResult:
    """Benchmark direct models on the same rolling forecast origins."""

    master = master_features.sort_index().replace([np.inf, -np.inf], np.nan)
    base_features = build_tabular_feature_frame(master)
    open_price = pd.to_numeric(master["gold_open"], errors="coerce")
    close = pd.to_numeric(master["gold_close"], errors="coerce")
    valid_origin = open_price.notna() & close.notna() & (close > 0)
    base_features = base_features.loc[valid_origin]
    open_price = open_price.loc[valid_origin]
    close = close.loc[valid_origin]

    maximum_horizon = OPEN_FORECAST_HORIZON
    minimum_rows = (
        TABULAR_FORECAST_TRAINING_WINDOW
        + n_windows * maximum_horizon
        + maximum_horizon
    )
    if len(base_features) < minimum_rows:
        raise ValueError(
            f"Tabular dataset has {len(base_features)} rows; "
            f"at least {minimum_rows} are required"
        )

    horizon_features: dict[int, pd.DataFrame] = {}
    horizon_targets: dict[int, pd.Series] = {}
    for horizon in range(1, OPEN_FORECAST_HORIZON + 1):
        features = pd.concat(
            [
                base_features,
                _future_calendar_frame(base_features.index, horizon),
            ],
            axis=1,
        )
        horizon_features[horizon] = features
        horizon_targets[horizon] = np.log(
            open_price.shift(-horizon) / close
        )

    feature_columns = tuple(horizon_features[1].columns)
    total_rows = len(base_features)
    cutoffs = [
        total_rows - (n_windows - window_index) * maximum_horizon - 1
        for window_index in range(n_windows)
    ]
    metric_rows: list[dict[str, float | int | str]] = []
    rolling_frames: list[pd.DataFrame] = []
    future_frames: list[pd.DataFrame] = []
    fitted_models: dict[
        str,
        DirectForecastModel | DirectForecastEnsemble,
    ] = {}
    training_seconds: dict[str, float] = {}
    importance_rows: list[dict[str, float | int | str]] = []
    future_dates = next_estimated_session_dates(
        base_features.index[-1],
        periods=OPEN_FORECAST_HORIZON,
    )

    for model_name in TABULAR_FORECAST_MODELS:
        started = time.perf_counter()
        rolling_rows: list[dict[str, float | int | str]] = []
        for cutoff in cutoffs:
            for horizon in range(1, OPEN_FORECAST_HORIZON + 1):
                training_start, training_end = _training_bounds(
                    cutoff,
                    horizon,
                )
                features = horizon_features[horizon]
                target = horizon_targets[horizon]
                train_x = features.iloc[training_start : training_end + 1]
                train_y = target.iloc[training_start : training_end + 1]
                valid_train = train_y.notna()
                estimator = _build_estimator(model_name)
                estimator.fit(
                    train_x.loc[valid_train, feature_columns],
                    train_y.loc[valid_train],
                )
                predicted_return = float(
                    estimator.predict(
                        features.iloc[[cutoff]].loc[:, feature_columns]
                    )[0]
                )
                rolling_rows.append(
                    {
                        "unique_id": "gold",
                        "ds": cutoff + horizon,
                        "cutoff": cutoff,
                        "cutoff_date": base_features.index[cutoff],
                        "forecast_date": base_features.index[cutoff + horizon],
                        "step": horizon,
                        "current_price": float(close.iloc[cutoff]),
                        "actual_price": float(open_price.iloc[cutoff + horizon]),
                        model_name: float(
                            close.iloc[cutoff] * np.exp(predicted_return)
                        ),
                    }
                )

        rolling = pd.DataFrame(rolling_rows)
        rolling_frames.append(rolling)
        metric_rows.extend(_metric_rows(rolling, model_name))

        production_estimators: dict[int, object] = {}
        future_rows: list[dict[str, float | int | str]] = []
        production_origin = total_rows - 1
        for horizon in range(1, OPEN_FORECAST_HORIZON + 1):
            training_start, training_end = _training_bounds(
                production_origin,
                horizon,
            )
            features = horizon_features[horizon]
            target = horizon_targets[horizon]
            train_x = features.iloc[training_start : training_end + 1]
            train_y = target.iloc[training_start : training_end + 1]
            valid_train = train_y.notna()
            estimator = _build_estimator(model_name)
            estimator.fit(
                train_x.loc[valid_train, feature_columns],
                train_y.loc[valid_train],
            )

            production_features = pd.concat(
                [
                    base_features.iloc[[-1]],
                    _future_calendar_frame(
                        base_features.index[-1:],
                        horizon,
                        production_date=future_dates[horizon - 1],
                    ),
                ],
                axis=1,
            ).loc[:, feature_columns]
            predicted_return = float(estimator.predict(production_features)[0])
            future_rows.append(
                {
                    "unique_id": "gold",
                    "ds": production_origin + horizon,
                    "step": horizon,
                    "forecast_date": future_dates[horizon - 1],
                    model_name: float(
                        close.iloc[-1] * np.exp(predicted_return)
                    ),
                }
            )
            production_estimators[horizon] = estimator

        fitted_models[model_name] = DirectForecastModel(
            model_name=model_name,
            estimators=production_estimators,
            feature_columns=feature_columns,
            training_window_sessions=TABULAR_FORECAST_TRAINING_WINDOW,
        )
        future_frames.append(pd.DataFrame(future_rows))
        importance_rows.extend(
            _extract_feature_importance(
                model_name,
                production_estimators,
                feature_columns,
            )
        )
        training_seconds[model_name] = time.perf_counter() - started

    for ensemble_name, component_models in TABULAR_FORECAST_ENSEMBLES.items():
        weights = np.repeat(1.0 / len(component_models), len(component_models))
        ensemble_rolling = rolling_frames[0][
            [
                "unique_id",
                "ds",
                "cutoff",
                "cutoff_date",
                "forecast_date",
                "step",
                "current_price",
                "actual_price",
            ]
        ].copy()
        ensemble_future = future_frames[0][
            ["unique_id", "ds", "step", "forecast_date"]
        ].copy()
        ensemble_rolling[ensemble_name] = sum(
            weight
            * next(
                frame[model_name]
                for frame, model_name in zip(
                    rolling_frames,
                    TABULAR_FORECAST_MODELS,
                )
                if model_name == component
            )
            for weight, component in zip(weights, component_models)
        )
        ensemble_future[ensemble_name] = sum(
            weight
            * next(
                frame[model_name]
                for frame, model_name in zip(
                    future_frames,
                    TABULAR_FORECAST_MODELS,
                )
                if model_name == component
            )
            for weight, component in zip(weights, component_models)
        )
        rolling_frames.append(ensemble_rolling)
        future_frames.append(ensemble_future)
        metric_rows.extend(_metric_rows(ensemble_rolling, ensemble_name))
        fitted_models[ensemble_name] = DirectForecastEnsemble(
            model_name=ensemble_name,
            component_models=tuple(component_models),
            weights=tuple(float(value) for value in weights),
        )
        training_seconds[ensemble_name] = float(
            sum(training_seconds[component] for component in component_models)
        )

    rolling_predictions = rolling_frames[0]
    for frame in rolling_frames[1:]:
        rolling_predictions = rolling_predictions.merge(
            frame,
            on=[
                "unique_id",
                "ds",
                "cutoff",
                "cutoff_date",
                "forecast_date",
                "step",
                "current_price",
                "actual_price",
            ],
            how="inner",
        )

    future_predictions = future_frames[0]
    for frame in future_frames[1:]:
        future_predictions = future_predictions.merge(
            frame,
            on=["unique_id", "ds", "step", "forecast_date"],
            how="inner",
        )
    future_predictions["as_of_date"] = base_features.index[-1]

    return TabularBenchmarkResult(
        metrics=pd.DataFrame(metric_rows),
        rolling_predictions=rolling_predictions,
        future_predictions=future_predictions,
        fitted_models=fitted_models,
        training_seconds=training_seconds,
        feature_columns=feature_columns,
        feature_importance=pd.DataFrame(importance_rows),
        training_rows=min(
            TABULAR_FORECAST_TRAINING_WINDOW,
            total_rows - OPEN_FORECAST_HORIZON,
        ),
        training_start_date=base_features.index[
            max(0, total_rows - TABULAR_FORECAST_TRAINING_WINDOW)
        ],
        training_end_date=base_features.index[-1],
    )


def predict_direct_model(
    model: DirectForecastModel,
    master_features: pd.DataFrame,
) -> pd.DataFrame:
    """Generate production forecasts from a serialized direct model."""

    master = master_features.sort_index()
    base_features = build_tabular_feature_frame(master)
    close = pd.to_numeric(master["gold_close"], errors="coerce")
    valid_origin = (
        pd.to_numeric(master["gold_open"], errors="coerce").notna()
        & close.notna()
        & (close > 0)
    )
    base_features = base_features.loc[valid_origin]
    close = close.loc[valid_origin]
    future_dates = next_estimated_session_dates(
        base_features.index[-1],
        periods=OPEN_FORECAST_HORIZON,
    )
    rows: list[dict[str, float | int | str | pd.Timestamp]] = []
    for horizon, estimator in sorted(model.estimators.items()):
        features = pd.concat(
            [
                base_features.iloc[[-1]],
                _future_calendar_frame(
                    base_features.index[-1:],
                    horizon,
                    production_date=future_dates[horizon - 1],
                ),
            ],
            axis=1,
        ).loc[:, model.feature_columns]
        predicted_return = float(estimator.predict(features)[0])
        rows.append(
            {
                "unique_id": "gold",
                "step": horizon,
                "forecast_date": future_dates[horizon - 1],
                model.model_name: float(close.iloc[-1] * np.exp(predicted_return)),
            }
        )
    return pd.DataFrame(rows)


__all__ = [
    "DirectForecastModel",
    "DirectForecastEnsemble",
    "TabularBenchmarkResult",
    "benchmark_tabular_models",
    "build_tabular_feature_frame",
    "predict_direct_model",
]
