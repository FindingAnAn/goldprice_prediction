"""
src/modeling/train.py
======================
Train candidate models, optionally tune them with Optuna, and persist the best one.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso, Ridge
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.pipelines.eda_data import combine_with_targets, load_master_features, load_target_labels
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

MODELS_DIR = Path("models")
MODELS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class TrainResult:
    name: str
    model: object
    cv_rmse: float
    test_rmse: float
    params: dict[str, object]


def time_series_train_test_split(df: pd.DataFrame, test_size: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame]:
    if df.empty:
        raise ValueError("Cannot split an empty DataFrame")

    split_index = max(1, int(len(df) * (1 - test_size)))
    split_index = min(split_index, len(df) - 1)
    return df.iloc[:split_index].copy(), df.iloc[split_index:].copy()


def build_training_frame(
    master_features: pd.DataFrame | None = None,
    target_labels: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Join feature and target tables into a single modeling frame."""

    if master_features is None:
        master_features = load_master_features()
    if target_labels is None:
        target_labels = load_target_labels()

    return combine_with_targets(master_features, target_labels)


def infer_feature_columns(df: pd.DataFrame, target_col: str) -> list[str]:
    feature_cols: list[str] = []
    for column in df.columns:
        if column == target_col:
            continue
        if pd.api.types.is_numeric_dtype(df[column]):
            feature_cols.append(column)
    return feature_cols


def _lazy_import_optional_models() -> dict[str, object]:
    candidates: dict[str, object] = {
        "ridge": Pipeline(
            [("scaler", StandardScaler()), ("model", Ridge(alpha=1.0))]
        ),
        "lasso": Pipeline(
            [("scaler", StandardScaler()), ("model", Lasso(alpha=0.01, max_iter=10_000))]
        ),
        "rf": RandomForestRegressor(random_state=42, n_estimators=200),
    }

    try:
        from lightgbm import LGBMRegressor

        candidates["lgbm"] = LGBMRegressor(random_state=42, n_estimators=200)
    except Exception:
        logger.info("lightgbm is unavailable; skipping LGBM candidate")

    try:
        from xgboost import XGBRegressor

        candidates["xgb"] = XGBRegressor(random_state=42, n_estimators=200, verbosity=0)
    except Exception:
        logger.info("xgboost is unavailable; skipping XGB candidate")

    return candidates


def _score_model(model: object, X_train: np.ndarray, y_train: np.ndarray, random_state: int) -> float:
    tscv = TimeSeriesSplit(n_splits=3)
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
) -> TrainResult:
    params: dict[str, object] = {}

    if use_optuna:
        model, params = tune_candidate(name, model, X_train, y_train, random_state=random_state, n_trials=tuning_trials)

    cv_rmse = _score_model(model, X_train, y_train, random_state)
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    test_rmse = float(np.sqrt(mean_squared_error(y_test, predictions)))

    return TrainResult(name=name, model=model, cv_rmse=cv_rmse, test_rmse=test_rmse, params=params)


def tune_candidate(
    name: str,
    model: object,
    X_train: np.ndarray,
    y_train: np.ndarray,
    random_state: int = 42,
    n_trials: int = 10,
) -> tuple[object, dict[str, object]]:
    """Tune a candidate estimator with Optuna when available.

    If Optuna or a model-specific tuning space is unavailable, the original model is returned.
    """

    try:
        import optuna
    except Exception:
        logger.info("optuna is unavailable; skipping tuning for %s", name)
        return model, {}

    def objective(trial: object) -> float:
        tuned_model = _clone_and_tune(name, model, trial, random_state=random_state)
        return _score_model(tuned_model, X_train, y_train, random_state)

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
    tuned_params.setdefault("random_state", random_state)
    return _clone_model(model, tuned_params)


def _clone_model(model: object, params: dict[str, object]) -> object:
    if hasattr(model, "set_params"):
        return model.set_params(**params)

    raise TypeError(f"Unsupported model type for tuning: {type(model)!r}")


def _sample_params(name: str, trial: object, random_state: int) -> dict[str, object]:
    import optuna  # type: ignore[import-not-found]

    if name == "ridge":
        return {"model__alpha": trial.suggest_float("model__alpha", 0.01, 10.0, log=True)}
    if name == "lasso":
        return {"model__alpha": trial.suggest_float("model__alpha", 0.0001, 1.0, log=True)}
    if name == "rf":
        return {
            "n_estimators": trial.suggest_int("n_estimators", 100, 400),
            "max_depth": trial.suggest_int("max_depth", 2, 12),
            "min_samples_split": trial.suggest_int("min_samples_split", 2, 10),
            "random_state": random_state,
        }
    if name == "lgbm":
        return {
            "n_estimators": trial.suggest_int("n_estimators", 100, 400),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 15, 63),
            "random_state": random_state,
        }
    if name == "xgb":
        return {
            "n_estimators": trial.suggest_int("n_estimators", 100, 400),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "max_depth": trial.suggest_int("max_depth", 2, 8),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "random_state": random_state,
            "verbosity": 0,
        }

    raise ValueError(f"Unknown candidate name: {name}")


def train_and_select_best(
    df: pd.DataFrame | None = None,
    feature_cols: list[str] | None = None,
    target_col: str = "next_1_day_price",
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
        df = build_training_frame()

    if target_col not in df.columns:
        raise KeyError(f"Target column {target_col!r} was not found in the training frame")

    if feature_cols is None:
        feature_cols = infer_feature_columns(df, target_col)

    modeling_frame = df.dropna(subset=feature_cols + [target_col]).copy()
    modeling_frame = modeling_frame.sort_index()

    train_df, test_df = time_series_train_test_split(modeling_frame, test_size=test_size)

    X_train = train_df[feature_cols].to_numpy()
    y_train = train_df[target_col].to_numpy()
    X_test = test_df[feature_cols].to_numpy()
    y_test = test_df[target_col].to_numpy()

    candidates = candidate_factory() if candidate_factory is not None else _lazy_import_optional_models()
    if not candidates:
        raise RuntimeError("No candidate models are available")

    results: list[TrainResult] = []
    for name, model in candidates.items():
        try:
            logger.info("Training candidate model: %s", name)
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
            )
            logger.info("Candidate %s finished with CV RMSE %.4f", name, result.cv_rmse)
            results.append(result)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Candidate %s failed: %s", name, exc)

    if not results:
        raise RuntimeError("No candidate models succeeded during training")

    best = min(results, key=lambda item: item.cv_rmse)
    joblib.dump(best.model, MODELS_DIR / f"best_model_{best.name}.joblib")
    joblib.dump(best.model, MODELS_DIR / "best_model.joblib")
    logger.info("Selected best model: %s (CV RMSE %.4f, test RMSE %.4f)", best.name, best.cv_rmse, best.test_rmse)
    return best


def evaluate_holdout_model(
    model: object,
    df: pd.DataFrame,
    feature_cols: list[str] | None = None,
    target_col: str = "next_1_day_price",
    test_size: float = 0.2,
) -> dict[str, float]:
    """Evaluate a fitted model on a chronological holdout split."""

    if target_col not in df.columns:
        raise KeyError(f"Target column {target_col!r} was not found in the evaluation frame")

    if feature_cols is None:
        feature_cols = infer_feature_columns(df, target_col)

    evaluation_frame = df.dropna(subset=feature_cols + [target_col]).copy().sort_index()
    train_df, test_df = time_series_train_test_split(evaluation_frame, test_size=test_size)
    X_test = test_df[feature_cols].to_numpy()
    y_test = test_df[target_col].to_numpy()
    predictions = model.predict(X_test)
    rmse = float(np.sqrt(mean_squared_error(y_test, predictions)))
    return {"rmse": rmse}


__all__ = [
    "TrainResult",
    "build_training_frame",
    "infer_feature_columns",
    "evaluate_holdout_model",
    "time_series_train_test_split",
    "train_and_select_best",
    "tune_candidate",
]
