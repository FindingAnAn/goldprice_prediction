"""
src/modeling/evaluate.py
========================
Evaluation helpers for regression models.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np

import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class EvalResult:
    rmse: float
    mae: float
    r2: float


def compute_metrics(y_true: pd.Series | list[float], y_pred: pd.Series | list[float]) -> EvalResult:
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))
    return EvalResult(rmse=rmse, mae=mae, r2=r2)


def evaluate_model(model: object, X: pd.DataFrame, y: pd.Series) -> EvalResult:
    predictions = model.predict(X.to_numpy())
    result = compute_metrics(y, predictions)
    logger.info("Evaluation metrics - RMSE: %.4f | MAE: %.4f | R2: %.4f", result.rmse, result.mae, result.r2)
    return result


def rank_results(results: list[tuple[str, EvalResult]]) -> tuple[str, EvalResult]:
    if not results:
        raise ValueError("No results to rank")
    return min(results, key=lambda item: item[1].rmse)


__all__ = ["EvalResult", "compute_metrics", "evaluate_model", "rank_results"]
