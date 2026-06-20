"""
src/modeling/train.py
======================
Train candidate models, optionally tune them with Optuna, and persist the best one.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Callable

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Lasso, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.inspection import permutation_importance
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config.settings import (
    POINT_IN_TIME_UNSAFE_FEATURE_COLUMNS,
    TARGET_COLUMN,
    TARGET_LABEL_COLUMNS,
)
from src.pipelines.eda_data import combine_with_targets, load_master_features, load_target_labels
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

MODELS_DIR = Path("models")
MODELS_DIR.mkdir(parents=True, exist_ok=True)
MODEL_REPORT_DIR = Path("data/predictions")
TARGET_COLUMN_PATTERN = re.compile(
    r"^next_(?P<horizon>\d+)_day_(?:price|open|direction|price_change)$"
)


@dataclass(frozen=True)
class TrainResult:
    name: str
    model: object
    cv_rmse: float
    test_rmse: float
    params: dict[str, object]
    test_mae: float = float("nan")
    test_r2: float = float("nan")


class FeatureColumnRegressor(BaseEstimator, RegressorMixin):
    """Persistence baseline that returns one observed feature column."""

    def __init__(self, feature_index: int):
        self.feature_index = feature_index

    def fit(self, X: np.ndarray, y: np.ndarray) -> "FeatureColumnRegressor":
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.asarray(X[:, self.feature_index], dtype=float)


class ReturnTargetRegressor(BaseEstimator, RegressorMixin):
    """Learn a percentage return, then reconstruct the future price."""

    def __init__(self, base_estimator: object, current_price_index: int):
        self.base_estimator = base_estimator
        self.current_price_index = current_price_index

    def fit(self, X: np.ndarray, y: np.ndarray) -> "ReturnTargetRegressor":
        current_price = np.asarray(X[:, self.current_price_index], dtype=float)
        return_target = (np.asarray(y, dtype=float) / current_price - 1.0) * 100.0
        self.estimator_ = clone(self.base_estimator)
        self.estimator_.fit(X, return_target)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        current_price = np.asarray(X[:, self.current_price_index], dtype=float)
        predicted_return = np.asarray(self.estimator_.predict(X), dtype=float)
        return current_price * (1.0 + predicted_return / 100.0)


class AnalogReturnRegressor(BaseEstimator, RegressorMixin):
    """Reconstruct price from a precomputed historical-analog return."""

    def __init__(self, current_price_index: int, analog_return_index: int):
        self.current_price_index = current_price_index
        self.analog_return_index = analog_return_index

    def fit(self, X: np.ndarray, y: np.ndarray) -> "AnalogReturnRegressor":
        analog = np.asarray(X[:, self.analog_return_index], dtype=float)
        self.fallback_return_ = float(np.nanmedian(analog))
        if not np.isfinite(self.fallback_return_):
            self.fallback_return_ = 0.0
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        current_price = np.asarray(X[:, self.current_price_index], dtype=float)
        analog_return = np.asarray(X[:, self.analog_return_index], dtype=float)
        analog_return = np.where(
            np.isfinite(analog_return),
            analog_return,
            self.fallback_return_,
        )
        return current_price * (1.0 + analog_return / 100.0)


def time_series_train_test_split(
    df: pd.DataFrame,
    test_size: float = 0.2,
    gap: int = 0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a time-ordered DataFrame into train/test without shuffling.

    The split is chronological: the earliest ``1 - test_size`` fraction goes
    to training and the remainder to testing.

    Args:
        df: DataFrame to split (must not be empty).
        test_size: Fraction of rows for the test set.
        gap: Number of rows purged between train and test. For an N-step
            target, use ``gap=N`` so train labels cannot overlap test dates.

    Returns:
        Tuple of (train_df, test_df).

    Raises:
        ValueError: If *df* is empty.
    """
    if df.empty:
        raise ValueError("Cannot split an empty DataFrame")
    if not 0 < test_size < 1:
        raise ValueError("test_size must be between 0 and 1")
    if gap < 0:
        raise ValueError("gap must be non-negative")

    split_index = max(1, int(len(df) * (1 - test_size)))
    split_index = min(split_index, len(df) - 1)
    train_end = split_index - gap
    if train_end < 1:
        raise ValueError(
            f"Not enough rows ({len(df)}) for test_size={test_size} and gap={gap}"
        )
    return df.iloc[:train_end].copy(), df.iloc[split_index:].copy()


def build_training_frame(
    master_features: pd.DataFrame | None = None,
    target_labels: pd.DataFrame | None = None,
    target_col: str = TARGET_COLUMN,
) -> pd.DataFrame:
    """Build a leakage-safe modeling frame with one target column."""

    if master_features is None:
        master_features = load_master_features()
    if target_labels is None:
        target_labels = load_target_labels(target_col=target_col)
    if target_col not in target_labels.columns:
        raise KeyError(f"Target column {target_col!r} was not found in target labels")

    return combine_with_targets(master_features, target_labels[[target_col]])


def infer_forecast_horizon(target_col: str) -> int:
    """Extract the number of future observations represented by a target."""

    match = TARGET_COLUMN_PATTERN.fullmatch(target_col)
    return int(match.group("horizon")) if match else 0


def infer_feature_columns(df: pd.DataFrame, target_col: str) -> list[str]:
    """Return numeric feature columns while excluding every future label.

    Args:
        df: DataFrame to inspect.
        target_col: Column name to exclude from features.

    Returns:
        List of numeric column names suitable as model features.
    """
    feature_cols: list[str] = []
    for column in df.columns:
        if column == target_col or column in TARGET_LABEL_COLUMNS:
            continue
        if TARGET_COLUMN_PATTERN.fullmatch(column):
            continue
        if column in POINT_IN_TIME_UNSAFE_FEATURE_COLUMNS:
            continue
        if pd.api.types.is_numeric_dtype(df[column]):
            feature_cols.append(column)
    return feature_cols


def validate_feature_columns(feature_cols: list[str]) -> None:
    """Fail fast when a future target column is passed as an input feature."""

    leakage_columns = [
        column
        for column in feature_cols
        if (
            column in TARGET_LABEL_COLUMNS
            or TARGET_COLUMN_PATTERN.fullmatch(column)
            or column in POINT_IN_TIME_UNSAFE_FEATURE_COLUMNS
        )
    ]
    if leakage_columns:
        raise ValueError(
            "Leakage-prone columns cannot be used as model features: "
            f"{sorted(leakage_columns)}"
        )


def _lazy_import_optional_models() -> dict[str, object]:
    median_imputer = SimpleImputer(strategy="median", add_indicator=True)
    candidates: dict[str, object] = {
        "ridge": Pipeline(
            [
                ("imputer", median_imputer),
                ("scaler", StandardScaler()),
                ("model", Ridge(alpha=1.0)),
            ]
        ),
        "lasso": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
                ("scaler", StandardScaler()),
                (
                    "model",
                    Lasso(
                        alpha=0.01,
                        max_iter=10_000,
                        tol=1e-3,
                        selection="random",
                        random_state=42,
                    ),
                ),
            ]
        ),
        "extra_trees": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
                (
                    "model",
                    ExtraTreesRegressor(
                        random_state=42,
                        n_estimators=200,
                        min_samples_leaf=2,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
        "hist_gbr": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
                (
                    "model",
                    HistGradientBoostingRegressor(
                        random_state=42,
                        learning_rate=0.05,
                        max_iter=300,
                        l2_regularization=1.0,
                    ),
                ),
            ]
        ),
        "rf": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
                (
                    "model",
                    RandomForestRegressor(
                        random_state=42,
                        n_estimators=200,
                        min_samples_leaf=2,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }

    try:
        from lightgbm import LGBMRegressor

        candidates["lgbm"] = LGBMRegressor(
            random_state=42,
            n_estimators=500,
            learning_rate=0.03,
            n_jobs=-1,
            verbosity=-1,
        )
    except Exception:
        logger.info("lightgbm is unavailable; skipping LGBM candidate")

    try:
        from xgboost import XGBRegressor

        candidates["xgb"] = XGBRegressor(
            random_state=42,
            n_estimators=500,
            learning_rate=0.03,
            max_depth=5,
            n_jobs=-1,
            verbosity=0,
        )
    except Exception:
        logger.info("xgboost is unavailable; skipping XGB candidate")

    try:
        from catboost import CatBoostRegressor

        candidates["catboost"] = CatBoostRegressor(
            random_seed=42,
            iterations=500,
            learning_rate=0.03,
            depth=6,
            loss_function="RMSE",
            verbose=False,
            allow_writing_files=False,
        )
    except Exception:
        logger.info("catboost is unavailable; skipping CatBoost candidate")

    return candidates


def _score_model(
    model: object,
    X_train: np.ndarray,
    y_train: np.ndarray,
    forecast_horizon: int,
) -> float:
    tscv = TimeSeriesSplit(n_splits=3, gap=forecast_horizon)
    scores = cross_val_score(model, X_train, y_train, cv=tscv, scoring="neg_root_mean_squared_error")
    return float(-np.mean(scores))


def _fit_and_evaluate(
    name: str,
    model: object,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    random_state: int,
    use_optuna: bool,
    tuning_trials: int,
    forecast_horizon: int,
) -> TrainResult:
    params: dict[str, object] = {}

    if use_optuna and name != "persistence":
        model, params = tune_candidate(
            name,
            model,
            X_train,
            y_train,
            random_state=random_state,
            n_trials=tuning_trials,
            forecast_horizon=forecast_horizon,
        )

    cv_rmse = _score_model(model, X_train, y_train, forecast_horizon)
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    test_rmse = float(np.sqrt(mean_squared_error(y_test, predictions)))
    test_mae = float(mean_absolute_error(y_test, predictions))
    test_r2 = float(r2_score(y_test, predictions))

    return TrainResult(
        name=name,
        model=model,
        cv_rmse=cv_rmse,
        test_rmse=test_rmse,
        params=params,
        test_mae=test_mae,
        test_r2=test_r2,
    )


def tune_candidate(
    name: str,
    model: object,
    X_train: np.ndarray,
    y_train: np.ndarray,
    random_state: int = 42,
    n_trials: int = 10,
    forecast_horizon: int = 0,
) -> tuple[object, dict[str, object]]:
    """Tune a candidate estimator with Optuna when available.

    If Optuna or a model-specific tuning space is unavailable, the original model is returned.
    """

    try:
        import optuna
    except Exception:
        logger.info("Optuna unavailable, skipping tuning", extra={"candidate": name})
        return model, {}

    def objective(trial: object) -> float:
        tuned_model = _clone_and_tune(name, model, trial, random_state=random_state)
        return _score_model(tuned_model, X_train, y_train, forecast_horizon)

    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=n_trials)

    if study.best_trial is None:
        return model, {}

    best_params = dict(study.best_trial.params)
    tuned_model = _clone_and_tune_from_params(name, model, best_params, random_state=random_state)
    return tuned_model, best_params


def _clone_and_tune(
    name: str,
    model: object,
    trial: object,
    random_state: int,
) -> object:
    params = _sample_params(name, trial, random_state=random_state)
    return _clone_model(model, params)


def _clone_and_tune_from_params(
    name: str,
    model: object,
    params: dict[str, object],
    random_state: int,
) -> object:
    tuned_params = dict(params)
    if name.startswith("return_"):
        tuned_params = {
            f"base_estimator__{key}": value
            for key, value in tuned_params.items()
        }
    return _clone_model(model, tuned_params)


def _clone_model(model: object, params: dict[str, object]) -> object:
    if hasattr(model, "set_params"):
        return clone(model).set_params(**params)

    raise TypeError(f"Unsupported model type for tuning: {type(model)!r}")


def _sample_params(name: str, trial: object, random_state: int) -> dict[str, object]:
    is_return_model = name.startswith("return_")
    base_name = name.removeprefix("return_")

    if base_name == "ridge":
        params = {"model__alpha": trial.suggest_float("model__alpha", 0.01, 10.0, log=True)}
    elif base_name == "lasso":
        params = {"model__alpha": trial.suggest_float("model__alpha", 0.0001, 1.0, log=True)}
    elif base_name == "rf":
        params = {
            "model__n_estimators": trial.suggest_int(
                "model__n_estimators", 150, 500
            ),
            "model__max_depth": trial.suggest_int("model__max_depth", 3, 16),
            "model__min_samples_leaf": trial.suggest_int(
                "model__min_samples_leaf", 1, 8
            ),
        }
    elif base_name == "extra_trees":
        params = {
            "model__n_estimators": trial.suggest_int(
                "model__n_estimators", 150, 500
            ),
            "model__max_features": trial.suggest_float(
                "model__max_features", 0.4, 1.0
            ),
            "model__min_samples_leaf": trial.suggest_int(
                "model__min_samples_leaf", 1, 8
            ),
        }
    elif base_name == "hist_gbr":
        params = {
            "model__max_iter": trial.suggest_int("model__max_iter", 150, 500),
            "model__learning_rate": trial.suggest_float(
                "model__learning_rate", 0.01, 0.15, log=True
            ),
            "model__max_leaf_nodes": trial.suggest_int(
                "model__max_leaf_nodes", 15, 63
            ),
            "model__l2_regularization": trial.suggest_float(
                "model__l2_regularization", 1e-4, 10.0, log=True
            ),
        }
    elif base_name == "lgbm":
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 100, 400),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 15, 63),
            "random_state": random_state,
        }
    elif base_name == "xgb":
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 100, 400),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "max_depth": trial.suggest_int("max_depth", 2, 8),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "random_state": random_state,
            "verbosity": 0,
        }
    elif base_name == "catboost":
        params = {
            "iterations": trial.suggest_int("iterations", 200, 700),
            "learning_rate": trial.suggest_float(
                "learning_rate", 0.01, 0.15, log=True
            ),
            "depth": trial.suggest_int("depth", 4, 9),
            "l2_leaf_reg": trial.suggest_float(
                "l2_leaf_reg", 1e-3, 10.0, log=True
            ),
        }
    else:
        raise ValueError(f"Unknown candidate name: {name}")

    if is_return_model:
        return {f"base_estimator__{key}": value for key, value in params.items()}
    return params


def train_and_select_best(
    df: pd.DataFrame | None = None,
    feature_cols: list[str] | None = None,
    target_col: str = TARGET_COLUMN,
    test_size: float = 0.2,
    random_state: int = 42,
    use_optuna: bool = False,
    tuning_trials: int = 10,
    candidate_factory: Callable[[], dict[str, object]] | None = None,
) -> TrainResult:
    """Train candidate models and return the best one by CV RMSE.

    The returned model is also persisted to `models/best_model.joblib`.
    """

    if df is None:
        df = build_training_frame(target_col=target_col)

    if target_col not in df.columns:
        raise KeyError(f"Target column {target_col!r} was not found in the training frame")

    if feature_cols is None:
        feature_cols = infer_feature_columns(df, target_col)
    validate_feature_columns(feature_cols)
    if not feature_cols:
        raise ValueError("No numeric feature columns are available")

    required_observed = [
        column
        for column in ("gold_close", "gold_open", "gold_high", "gold_low")
        if column in feature_cols
    ]
    modeling_frame = df.dropna(
        subset=required_observed + [target_col]
    ).copy()
    modeling_frame = modeling_frame.sort_index()

    forecast_horizon = infer_forecast_horizon(target_col)
    train_df, test_df = time_series_train_test_split(
        modeling_frame,
        test_size=test_size,
        gap=forecast_horizon,
    )

    X_train = train_df[feature_cols].to_numpy()
    y_train = train_df[target_col].to_numpy()
    X_test = test_df[feature_cols].to_numpy()
    y_test = test_df[target_col].to_numpy()

    candidates = candidate_factory() if candidate_factory is not None else _lazy_import_optional_models()
    if "gold_close" in feature_cols:
        current_price_index = feature_cols.index("gold_close")
        if candidate_factory is None and target_col.endswith("_price"):
            direct_linear = {
                name: model
                for name, model in candidates.items()
                if name in {"ridge", "lasso"}
            }
            return_models = {
                f"return_{name}": ReturnTargetRegressor(
                    base_estimator=model,
                    current_price_index=current_price_index,
                )
                for name, model in candidates.items()
            }
            candidates = {**direct_linear, **return_models}
        analog_column = f"same_doy_return_{forecast_horizon}d_mean"
        if analog_column in feature_cols and target_col.endswith("_price"):
            candidates = {
                "same_doy_analog": AnalogReturnRegressor(
                    current_price_index=current_price_index,
                    analog_return_index=feature_cols.index(analog_column),
                ),
                **candidates,
            }
        candidates = {
            "persistence": FeatureColumnRegressor(
                feature_index=current_price_index
            ),
            **candidates,
        }
    if not candidates:
        raise RuntimeError("No candidate models are available")

    results: list[TrainResult] = []
    for name, model in candidates.items():
        try:
            logger.info("Training candidate model", extra={"candidate_name": name})
            result = _fit_and_evaluate(
                name=name,
                model=model,
                X_train=X_train,
                y_train=y_train,
                X_test=X_test,
                y_test=y_test,
                random_state=random_state,
                use_optuna=use_optuna,
                tuning_trials=tuning_trials,
                forecast_horizon=forecast_horizon,
            )
            logger.info(
                "Candidate finished",
                extra={
                    "candidate_name": name,
                    "cv_rmse": f"{result.cv_rmse:.4f}",
                },
            )
            results.append(result)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception(
                "Candidate failed",
                extra={"candidate_name": name, "error": str(exc)},
            )

    if not results:
        raise RuntimeError("No candidate models succeeded during training")

    best = min(results, key=lambda item: item.cv_rmse)
    leaderboard = pd.DataFrame(
        [
            {
                "model": result.name,
                "cv_rmse": result.cv_rmse,
                "test_rmse": result.test_rmse,
                "test_mae": result.test_mae,
                "test_r2": result.test_r2,
                "params": result.params,
            }
            for result in results
        ]
    ).sort_values("cv_rmse")
    leaderboard_path = MODEL_REPORT_DIR / "model_leaderboard.csv"
    leaderboard_path.parent.mkdir(parents=True, exist_ok=True)
    leaderboard.to_csv(leaderboard_path, index=False)

    importance = permutation_importance(
        best.model,
        X_test,
        y_test,
        scoring="neg_root_mean_squared_error",
        n_repeats=5,
        random_state=random_state,
        n_jobs=-1,
    )
    pd.DataFrame(
        {
            "feature": feature_cols,
            "importance_mean": importance.importances_mean,
            "importance_std": importance.importances_std,
        }
    ).sort_values("importance_mean", ascending=False).to_csv(
        MODEL_REPORT_DIR / "permutation_importance.csv",
        index=False,
    )

    evaluation_model = best.model
    try:
        setattr(evaluation_model, "_gold_feature_cols", list(feature_cols))
        setattr(evaluation_model, "_gold_target_col", target_col)
        setattr(evaluation_model, "_gold_forecast_horizon", forecast_horizon)
        setattr(evaluation_model, "_gold_fit_scope", "train_only")
    except Exception:
        logger.warning("Could not attach metadata to the holdout model")
    joblib.dump(evaluation_model, MODELS_DIR / "best_model_holdout.joblib")

    production_model = clone(evaluation_model)
    production_model.fit(
        modeling_frame[feature_cols].to_numpy(),
        modeling_frame[target_col].to_numpy(),
    )
    best = TrainResult(
        name=best.name,
        model=production_model,
        cv_rmse=best.cv_rmse,
        test_rmse=best.test_rmse,
        params=best.params,
        test_mae=best.test_mae,
        test_r2=best.test_r2,
    )
    try:
        setattr(best.model, "_gold_feature_cols", list(feature_cols))
        setattr(best.model, "_gold_target_col", target_col)
        setattr(best.model, "_gold_forecast_horizon", forecast_horizon)
        setattr(best.model, "_gold_fit_scope", "full_labeled_data")
    except Exception:
        logger.warning("Could not attach modeling metadata to the selected model")
    joblib.dump(best.model, MODELS_DIR / f"best_model_{best.name}.joblib")
    joblib.dump(best.model, MODELS_DIR / "best_model.joblib")
    logger.info(
        "Selected best model",
        extra={
            "model_name": best.name,
            "cv_rmse": f"{best.cv_rmse:.4f}",
            "test_rmse": f"{best.test_rmse:.4f}",
        },
    )
    return best


def evaluate_holdout_model(
    model: object,
    df: pd.DataFrame,
    feature_cols: list[str] | None = None,
    target_col: str = TARGET_COLUMN,
    test_size: float = 0.2,
) -> dict[str, float]:
    """Evaluate a fitted model on a chronological holdout split."""

    if getattr(model, "_gold_fit_scope", None) == "full_labeled_data":
        raise ValueError(
            "Cannot evaluate the production model on its historical holdout: "
            "it was refit on all labeled data. Use models/best_model_holdout.joblib."
        )

    if target_col not in df.columns:
        raise KeyError(f"Target column {target_col!r} was not found in the evaluation frame")

    if feature_cols is None:
        feature_cols = infer_feature_columns(df, target_col)
    validate_feature_columns(feature_cols)

    required_observed = [
        column
        for column in ("gold_close", "gold_open", "gold_high", "gold_low")
        if column in feature_cols
    ]
    evaluation_frame = (
        df.dropna(subset=required_observed + [target_col])
        .copy()
        .sort_index()
    )
    forecast_horizon = infer_forecast_horizon(target_col)
    _, test_df = time_series_train_test_split(
        evaluation_frame,
        test_size=test_size,
        gap=forecast_horizon,
    )
    X_test = test_df[feature_cols].to_numpy()
    y_test = test_df[target_col].to_numpy()
    predictions = model.predict(X_test)
    rmse = float(np.sqrt(mean_squared_error(y_test, predictions)))
    return {"rmse": rmse}


__all__ = [
    "TrainResult",
    "FeatureColumnRegressor",
    "ReturnTargetRegressor",
    "AnalogReturnRegressor",
    "build_training_frame",
    "infer_feature_columns",
    "infer_forecast_horizon",
    "validate_feature_columns",
    "evaluate_holdout_model",
    "time_series_train_test_split",
    "train_and_select_best",
    "tune_candidate",
]
