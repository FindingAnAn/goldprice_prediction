"""Leakage-safe AutoGluon benchmark for the direct N-session target."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from config.settings import TARGET_COLUMN
from src.modeling.train import (
    build_training_frame,
    infer_feature_columns,
    infer_forecast_horizon,
    time_series_train_test_split,
    validate_feature_columns,
)


@dataclass(frozen=True)
class AutoGluonBenchmarkResult:
    model_name: str
    model_path: Path
    rmse: float
    mae: float
    r2: float


def _require_autogluon() -> Any:
    try:
        from autogluon.tabular import TabularPredictor
    except ImportError as exc:
        raise RuntimeError(
            "AutoGluon is not installed. Install requirements-autogluon.txt "
            "before running this benchmark."
        ) from exc
    return TabularPredictor


def benchmark_autogluon(
    df: pd.DataFrame | None = None,
    feature_cols: list[str] | None = None,
    target_col: str = TARGET_COLUMN,
    test_size: float = 0.2,
    validation_size: float = 0.2,
    time_limit: int = 600,
    presets: str = "medium_quality",
    model_path: Path | None = None,
) -> AutoGluonBenchmarkResult:
    """Train AutoGluon and score it on a final unseen chronological holdout."""

    tabular_predictor = _require_autogluon()
    if df is None:
        df = build_training_frame(target_col=target_col)
    if target_col not in df.columns:
        raise KeyError(f"Target column {target_col!r} was not found")

    feature_cols = feature_cols or infer_feature_columns(df, target_col)
    validate_feature_columns(feature_cols)
    horizon = infer_forecast_horizon(target_col)
    if model_path is None:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        model_path = Path(f"models/autogluon_{target_col}_{run_id}")

    modeling_frame = (
        df[feature_cols + [target_col]]
        .dropna()
        .sort_index()
    )
    train_validation, test = time_series_train_test_split(
        modeling_frame,
        test_size=test_size,
        gap=horizon,
    )
    train, validation = time_series_train_test_split(
        train_validation,
        test_size=validation_size,
        gap=horizon,
    )

    predictor = tabular_predictor(
        label=target_col,
        problem_type="regression",
        eval_metric="root_mean_squared_error",
        path=str(model_path),
    ).fit(
        train_data=train.reset_index(drop=True),
        tuning_data=validation.reset_index(drop=True),
        time_limit=time_limit,
        presets=presets,
        use_bag_holdout=True,
    )

    predictions = predictor.predict(test[feature_cols].reset_index(drop=True))
    y_test = test[target_col].to_numpy()
    rmse = float(np.sqrt(mean_squared_error(y_test, predictions)))
    mae = float(mean_absolute_error(y_test, predictions))
    r2 = float(r2_score(y_test, predictions))

    return AutoGluonBenchmarkResult(
        model_name=str(predictor.model_best),
        model_path=model_path,
        rmse=rmse,
        mae=mae,
        r2=r2,
    )


__all__ = ["AutoGluonBenchmarkResult", "benchmark_autogluon"]
