"""
src/modeling/predict.py
=======================
Load a persisted model and produce predictions for the newest available rows.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd

from src.pipelines.eda_data import load_master_features
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

MODELS_DIR = Path("models")
PRED_DIR = Path("data/predictions")
PRED_DIR.mkdir(parents=True, exist_ok=True)


def load_best_model(path: Path | None = None) -> object:
    """Load a persisted model from disk.

    Args:
        path: Path to the model file. Defaults to ``models/best_model.joblib``.

    Returns:
        The deserialized model object (typically a scikit-learn estimator).

    Raises:
        FileNotFoundError: If the model file does not exist.
    """
    model_path = Path(path) if path is not None else MODELS_DIR / "best_model.joblib"
    logger.info("Loading model", extra={"path": str(model_path)})
    return joblib.load(model_path)


def predict_frame(
    model: object,
    feature_frame: pd.DataFrame,
    feature_cols: list[str] | None = None,
    latest_n: int = 1,
    persist: bool = True,
    output_dir: Path | None = None,
) -> pd.DataFrame:
    """Generate predictions for the most recent rows in a feature frame."""

    if feature_frame.empty:
        raise ValueError("feature_frame is empty")

    frame = feature_frame.sort_index().tail(latest_n).copy()
    cols = feature_cols or list(frame.columns)
    missing_cols = [column for column in cols if column not in frame.columns]
    if missing_cols:
        raise KeyError(f"Missing feature columns for prediction: {missing_cols}")

    predictions = model.predict(frame[cols].to_numpy())
    output = pd.DataFrame(index=frame.index)
    output["prediction"] = predictions
    output.index.name = "date"

    if persist:
        directory = output_dir or PRED_DIR
        directory.mkdir(parents=True, exist_ok=True)
        output_path = directory / f"predictions_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.csv"
        output.to_csv(output_path)
        logger.info("Saved predictions to %s", output_path)

    return output


def predict_latest(
    model: object | None = None,
    model_path: Path | None = None,
    feature_frame: pd.DataFrame | None = None,
    feature_cols: list[str] | None = None,
    latest_n: int = 1,
    persist: bool = True,
    output_dir: Path | None = None,
) -> pd.DataFrame:
    """Convenience wrapper that loads the latest feature frame from the database."""

    if feature_frame is None:
        feature_frame = load_master_features()

    if model is None:
        model = load_best_model(model_path)

    return predict_frame(
        model=model,
        feature_frame=feature_frame,
        feature_cols=feature_cols,
        latest_n=latest_n,
        persist=persist,
        output_dir=output_dir,
    )


__all__ = ["load_best_model", "predict_frame", "predict_latest"]
