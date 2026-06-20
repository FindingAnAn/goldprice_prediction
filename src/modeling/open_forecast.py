"""Leakage-safe multi-output forecast of the next 10 gold opening prices."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import time
from typing import Callable

import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config.settings import (
    OPEN_FORECAST_CV_SPLITS,
    OPEN_FORECAST_HORIZON,
    OPEN_FORECAST_MODEL_CONFIG,
    OPEN_FORECAST_RANDOM_SEED,
    OPEN_FORECAST_TEST_SIZE,
    OPEN_TARGET_COLUMNS,
)
from src.modeling.train import (
    infer_feature_columns,
    time_series_train_test_split,
    validate_feature_columns,
)
from src.pipelines.eda_data import load_master_features
from src.data.storage.postgres_client import get_engine
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class MultiHorizonPersistenceRegressor(BaseEstimator, RegressorMixin):
    """Repeat the latest known close for every future opening price."""

    def __init__(self, current_price_index: int, horizon: int):
        self.current_price_index = current_price_index
        self.horizon = horizon

    def fit(self, X: np.ndarray, y: np.ndarray) -> "MultiHorizonPersistenceRegressor":
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        current = np.asarray(X[:, self.current_price_index], dtype=float)
        return np.repeat(current[:, None], self.horizon, axis=1)


class MultiHorizonReturnRegressor(BaseEstimator, RegressorMixin):
    """Learn future-open returns relative to the current close."""

    def __init__(self, base_estimator: object, current_price_index: int):
        self.base_estimator = base_estimator
        self.current_price_index = current_price_index

    def fit(self, X: np.ndarray, y: np.ndarray) -> "MultiHorizonReturnRegressor":
        current = np.asarray(X[:, self.current_price_index], dtype=float)
        returns = (np.asarray(y, dtype=float) / current[:, None] - 1.0) * 100.0
        self.estimator_ = clone(self.base_estimator)
        self.estimator_.fit(X, returns)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        current = np.asarray(X[:, self.current_price_index], dtype=float)
        returns = np.asarray(self.estimator_.predict(X), dtype=float)
        return current[:, None] * (1.0 + returns / 100.0)


@dataclass(frozen=True)
class OpenForecastTrainingResult:
    selected_name: str
    production_model: object
    holdout_model: object
    feature_columns: list[str]
    leaderboard: pd.DataFrame
    metrics: pd.DataFrame
    holdout_predictions: pd.DataFrame
    interval_80: np.ndarray
    interval_95: np.ndarray
    train_rows: int
    validation_rows: int
    test_rows: int


def load_open_targets() -> pd.DataFrame:
    columns = ", ".join(OPEN_TARGET_COLUMNS)
    query = f"""
        SELECT date, {columns}
        FROM features.target_labels
        ORDER BY date
    """
    engine = get_engine()
    with engine.connect() as connection:
        return pd.read_sql(
            query,
            connection,
            index_col="date",
            parse_dates=["date"],
        )


def build_open_training_frame(
    master_features: pd.DataFrame | None = None,
    targets: pd.DataFrame | None = None,
) -> pd.DataFrame:
    features = master_features if master_features is not None else load_master_features()
    target_frame = targets if targets is not None else load_open_targets()
    return features.join(target_frame[list(OPEN_TARGET_COLUMNS)], how="inner")


def _candidate_models(
    current_price_index: int,
    random_seed: int,
) -> dict[str, tuple[object, dict[str, object]]]:
    config = OPEN_FORECAST_MODEL_CONFIG
    ridge = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            ("scaler", StandardScaler()),
            ("model", Ridge(alpha=float(config["ridge_alpha"]))),
        ]
    )
    extra_trees = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            (
                "model",
                ExtraTreesRegressor(
                    n_estimators=int(config["extra_trees_estimators"]),
                    min_samples_leaf=int(config["extra_trees_min_samples_leaf"]),
                    max_features=float(config["extra_trees_max_features"]),
                    random_state=random_seed,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    random_forest = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=int(config["random_forest_estimators"]),
                    min_samples_leaf=int(config["random_forest_min_samples_leaf"]),
                    max_features=float(config["random_forest_max_features"]),
                    random_state=random_seed,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    return {
        "persistence_close": (
            MultiHorizonPersistenceRegressor(
                current_price_index=current_price_index,
                horizon=OPEN_FORECAST_HORIZON,
            ),
            {},
        ),
        "return_ridge": (
            MultiHorizonReturnRegressor(ridge, current_price_index),
            {"ridge_alpha": config["ridge_alpha"]},
        ),
        "return_extra_trees": (
            MultiHorizonReturnRegressor(extra_trees, current_price_index),
            {
                "n_estimators": config["extra_trees_estimators"],
                "min_samples_leaf": config["extra_trees_min_samples_leaf"],
                "max_features": config["extra_trees_max_features"],
            },
        ),
        "return_random_forest": (
            MultiHorizonReturnRegressor(random_forest, current_price_index),
            {
                "n_estimators": config["random_forest_estimators"],
                "min_samples_leaf": config["random_forest_min_samples_leaf"],
                "max_features": config["random_forest_max_features"],
            },
        ),
    }


def _cv_rmse(
    model: object,
    X: np.ndarray,
    y: np.ndarray,
    n_splits: int,
) -> tuple[float, int]:
    scores: list[float] = []
    validation_rows = 0
    splitter = TimeSeriesSplit(
        n_splits=n_splits,
        gap=OPEN_FORECAST_HORIZON,
    )
    for train_index, validation_index in splitter.split(X):
        fold_model = clone(model)
        fold_model.fit(X[train_index], y[train_index])
        prediction = fold_model.predict(X[validation_index])
        scores.append(float(np.sqrt(mean_squared_error(y[validation_index], prediction))))
        validation_rows = max(validation_rows, len(validation_index))
    return float(np.mean(scores)), validation_rows


def _metric_records(
    model_name: str,
    split_name: str,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    current_close: np.ndarray,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for step in range(OPEN_FORECAST_HORIZON + 1):
        if step == 0:
            actual = y_true.reshape(-1)
            predicted = y_pred.reshape(-1)
            current = np.repeat(current_close, OPEN_FORECAST_HORIZON)
        else:
            actual = y_true[:, step - 1]
            predicted = y_pred[:, step - 1]
            current = current_close
        metric_values = {
            "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
            "mae": float(mean_absolute_error(actual, predicted)),
            "mape": float(np.mean(np.abs((actual - predicted) / actual)) * 100.0),
            "r2": float(r2_score(actual, predicted)),
            "direction_accuracy": (
                float("nan")
                if np.allclose(predicted, current)
                else float(
                    np.mean(
                        np.sign(predicted - current)
                        == np.sign(actual - current)
                    )
                )
            ),
        }
        for metric_name, metric_value in metric_values.items():
            rows.append(
                {
                    "model_name": model_name,
                    "split_name": split_name,
                    "horizon_step": step,
                    "metric_name": metric_name,
                    "metric_value": metric_value,
                    "sample_count": len(actual),
                }
            )
    return rows


def train_open_forecast(
    frame: pd.DataFrame | None = None,
    test_size: float = OPEN_FORECAST_TEST_SIZE,
    random_seed: int = OPEN_FORECAST_RANDOM_SEED,
    cv_splits: int = OPEN_FORECAST_CV_SPLITS,
) -> OpenForecastTrainingResult:
    training_frame = frame if frame is not None else build_open_training_frame()
    feature_columns = infer_feature_columns(
        training_frame,
        target_col=OPEN_TARGET_COLUMNS[0],
    )
    validate_feature_columns(feature_columns)
    required = [
        column
        for column in ("gold_close", "gold_open", "gold_high", "gold_low")
        if column in feature_columns
    ]
    modeling_frame = (
        training_frame.dropna(subset=required + list(OPEN_TARGET_COLUMNS))
        .sort_index()
        .copy()
    )
    train, test = time_series_train_test_split(
        modeling_frame,
        test_size=test_size,
        gap=OPEN_FORECAST_HORIZON,
    )
    X_train = train[feature_columns].to_numpy()
    y_train = train[list(OPEN_TARGET_COLUMNS)].to_numpy()
    X_test = test[feature_columns].to_numpy()
    y_test = test[list(OPEN_TARGET_COLUMNS)].to_numpy()
    current_train = train["gold_close"].to_numpy()
    current_test = test["gold_close"].to_numpy()
    current_price_index = feature_columns.index("gold_close")

    fitted: dict[str, object] = {}
    leaderboard_rows: list[dict[str, object]] = []
    metric_rows: list[dict[str, object]] = []
    prediction_rows: list[pd.DataFrame] = []
    validation_rows = 0

    for name, (model, parameters) in _candidate_models(
        current_price_index,
        random_seed,
    ).items():
        started = time.perf_counter()
        logger.info(
            "Candidate training started",
            extra={"stage": "model_training", "model_name": name},
        )
        cv_rmse, candidate_validation_rows = _cv_rmse(
            model,
            X_train,
            y_train,
            cv_splits,
        )
        validation_rows = max(validation_rows, candidate_validation_rows)
        model.fit(X_train, y_train)
        predicted_train = np.asarray(model.predict(X_train), dtype=float)
        predicted = np.asarray(model.predict(X_test), dtype=float)
        elapsed = time.perf_counter() - started
        fitted[name] = model
        train_metrics = _metric_records(
            name,
            "train",
            y_train,
            predicted_train,
            current_train,
        )
        holdout_metrics = _metric_records(
            name,
            "holdout",
            y_test,
            predicted,
            current_test,
        )
        metric_rows.extend(train_metrics)
        metric_rows.append(
            {
                "model_name": name,
                "split_name": "validation_cv",
                "horizon_step": 0,
                "metric_name": "rmse",
                "metric_value": cv_rmse,
                "sample_count": candidate_validation_rows,
            }
        )
        metric_rows.extend(holdout_metrics)
        overall_lookup = {
            row["metric_name"]: row["metric_value"]
            for row in holdout_metrics
            if row["horizon_step"] == 0
        }
        leaderboard_rows.append(
            {
                "model": name,
                "selected": False,
                "parameters": parameters,
                "cv_rmse": cv_rmse,
                "holdout_rmse": overall_lookup["rmse"],
                "holdout_mae": overall_lookup["mae"],
                "holdout_mape": overall_lookup["mape"],
                "holdout_r2": overall_lookup["r2"],
                "rmse_improvement_vs_persistence_pct": 0.0,
                "training_seconds": elapsed,
                "artifact_path": None,
            }
        )
        prediction_rows.append(
            pd.DataFrame(
                {
                    "as_of_date": np.repeat(test.index.to_numpy(), OPEN_FORECAST_HORIZON),
                    "model_name": name,
                    "forecast_step": np.tile(
                        np.arange(1, OPEN_FORECAST_HORIZON + 1),
                        len(test),
                    ),
                    "actual_open": y_test.reshape(-1),
                    "predicted_open": predicted.reshape(-1),
                    "current_close": np.repeat(current_test, OPEN_FORECAST_HORIZON),
                }
            )
        )
        logger.info(
            "Candidate training completed",
            extra={
                "stage": "model_training",
                "model_name": name,
                "cv_rmse": cv_rmse,
                "holdout_rmse": overall_lookup["rmse"],
                "duration_seconds": elapsed,
            },
        )

    leaderboard = pd.DataFrame(leaderboard_rows).sort_values("cv_rmse")
    persistence_rmse = float(
        leaderboard.loc[
            leaderboard["model"] == "persistence_close",
            "holdout_rmse",
        ].iloc[0]
    )
    leaderboard["rmse_improvement_vs_persistence_pct"] = (
        100.0
        * (persistence_rmse - leaderboard["holdout_rmse"])
        / persistence_rmse
    )
    selected_name = str(leaderboard.iloc[0]["model"])
    leaderboard.loc[leaderboard["model"] == selected_name, "selected"] = True
    holdout_model = fitted[selected_name]
    selected_predictions = np.asarray(holdout_model.predict(X_test), dtype=float)
    absolute_residuals = np.abs(y_test - selected_predictions)
    interval_80 = np.quantile(absolute_residuals, 0.80, axis=0)
    interval_95 = np.quantile(absolute_residuals, 0.95, axis=0)

    production_model = clone(holdout_model)
    production_model.fit(
        modeling_frame[feature_columns].to_numpy(),
        modeling_frame[list(OPEN_TARGET_COLUMNS)].to_numpy(),
    )
    metadata = {
        "_gold_feature_cols": list(feature_columns),
        "_gold_target_cols": list(OPEN_TARGET_COLUMNS),
        "_gold_forecast_horizon": OPEN_FORECAST_HORIZON,
        "_gold_fit_scope": "full_labeled_data",
        "_gold_model_name": selected_name,
        "_gold_interval_80": interval_80.tolist(),
        "_gold_interval_95": interval_95.tolist(),
    }
    for key, value in metadata.items():
        setattr(production_model, key, value)
    for key, value in {**metadata, "_gold_fit_scope": "train_only"}.items():
        setattr(holdout_model, key, value)

    return OpenForecastTrainingResult(
        selected_name=selected_name,
        production_model=production_model,
        holdout_model=holdout_model,
        feature_columns=feature_columns,
        leaderboard=leaderboard,
        metrics=pd.DataFrame(metric_rows),
        holdout_predictions=pd.concat(prediction_rows, ignore_index=True),
        interval_80=interval_80,
        interval_95=interval_95,
        train_rows=len(train),
        validation_rows=validation_rows,
        test_rows=len(test),
    )


def next_estimated_session_dates(
    as_of_date: date | pd.Timestamp,
    periods: int = OPEN_FORECAST_HORIZON,
) -> pd.DatetimeIndex:
    business_day = CustomBusinessDay(calendar=USFederalHolidayCalendar())
    return pd.date_range(
        start=pd.Timestamp(as_of_date) + business_day,
        periods=periods,
        freq=business_day,
    )


def predict_next_opens(
    model: object,
    feature_frame: pd.DataFrame | None = None,
) -> pd.DataFrame:
    features = feature_frame if feature_frame is not None else load_master_features()
    latest = features.sort_index().tail(1)
    feature_columns = list(getattr(model, "_gold_feature_cols"))
    missing = [column for column in feature_columns if column not in latest.columns]
    if missing:
        raise KeyError(f"Missing model features: {missing}")
    prediction = np.asarray(
        model.predict(latest[feature_columns].to_numpy()),
        dtype=float,
    ).reshape(-1)
    interval_80 = np.asarray(getattr(model, "_gold_interval_80"), dtype=float)
    interval_95 = np.asarray(getattr(model, "_gold_interval_95"), dtype=float)
    as_of_date = latest.index[-1]
    forecast_dates = next_estimated_session_dates(as_of_date)
    return pd.DataFrame(
        {
            "as_of_date": as_of_date.date(),
            "forecast_step": np.arange(1, OPEN_FORECAST_HORIZON + 1),
            "forecast_date": forecast_dates.date,
            "predicted_open": prediction,
            "lower_80": prediction - interval_80,
            "upper_80": prediction + interval_80,
            "lower_95": prediction - interval_95,
            "upper_95": prediction + interval_95,
            "is_estimated_date": True,
        }
    )


__all__ = [
    "MultiHorizonPersistenceRegressor",
    "MultiHorizonReturnRegressor",
    "OpenForecastTrainingResult",
    "build_open_training_frame",
    "load_open_targets",
    "next_estimated_session_dates",
    "predict_next_opens",
    "train_open_forecast",
]
