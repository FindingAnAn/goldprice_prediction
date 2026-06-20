"""Rolling-window benchmark for production sequence forecasting models."""

from __future__ import annotations

from dataclasses import dataclass
import time

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

from config.settings import (
    DEEP_FORECAST_HIST_EXOG,
    DEEP_FORECAST_HORIZONS,
    DEEP_FORECAST_INPUT_SIZE,
    DEEP_FORECAST_MIN_EXOG_COVERAGE,
    DEEP_FORECAST_MODELS,
    DEEP_FORECAST_VALIDATION_SIZE,
)
from src.pipelines.eda_data import load_master_features


@dataclass(frozen=True)
class SequenceBenchmarkResult:
    """Artifacts and diagnostics from the sequence-model benchmark."""

    metrics: pd.DataFrame
    rolling_predictions: pd.DataFrame
    future_predictions: pd.DataFrame
    fitted_forecasters: dict[str, object]
    training_seconds: dict[str, float]
    used_exogenous_features: tuple[str, ...]
    excluded_exogenous_features: tuple[str, ...]
    sequence_rows: int
    sequence_start_date: pd.Timestamp
    sequence_end_date: pd.Timestamp


def _prepare_sequence_data(
    master_features: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, tuple[str, ...], tuple[str, ...]]:
    """Build a causally imputed sequence frame without shortening to 3 years."""

    master = (
        master_features.copy()
        if master_features is not None
        else load_master_features()
    ).sort_index()
    master = master.replace([np.inf, -np.inf], np.nan)
    target_mask = master["gold_open"].notna()
    candidate_features = [
        column
        for column in DEEP_FORECAST_HIST_EXOG
        if column in master.columns
    ]
    coverage = master.loc[target_mask, candidate_features].notna().mean()
    used = tuple(
        column
        for column in candidate_features
        if float(coverage[column]) >= DEEP_FORECAST_MIN_EXOG_COVERAGE
    )
    excluded = tuple(
        column for column in candidate_features if column not in used
    )

    sequence = master.loc[target_mask, ["gold_open", *used]].copy()
    if used:
        sequence.loc[:, list(used)] = sequence.loc[:, list(used)].ffill()
    sequence = sequence.dropna(subset=["gold_open", *used])
    minimum_rows = DEEP_FORECAST_INPUT_SIZE + max(DEEP_FORECAST_HORIZONS) + 1
    if len(sequence) < minimum_rows:
        raise ValueError(
            f"Sequence dataset has {len(sequence)} rows; "
            f"at least {minimum_rows} are required"
        )

    neural_frame = pd.DataFrame(
        {
            "unique_id": "gold",
            "ds": np.arange(len(sequence), dtype=np.int64),
            "y": np.log(sequence["gold_open"].to_numpy(dtype=float)),
            **{
                column: sequence[column].to_numpy(dtype=float)
                for column in used
            },
        }
    )
    return sequence, neural_frame, used, excluded


def _build_model(
    model_name: str,
    historical_exogenous: tuple[str, ...],
    max_steps: int,
) -> object:
    from neuralforecast.models import NHITS, PatchTST, TiDE

    common = {
        "h": max(DEEP_FORECAST_HORIZONS),
        "input_size": DEEP_FORECAST_INPUT_SIZE,
        "scaler_type": "robust",
        "max_steps": max_steps,
        "val_check_steps": min(25, max_steps),
        "early_stop_patience_steps": 3,
        "random_seed": 42,
        "enable_progress_bar": False,
        "logger": False,
    }
    if model_name == "TiDE":
        return TiDE(
            **common,
            hist_exog_list=list(historical_exogenous),
            hidden_size=128,
            decoder_output_dim=32,
            temporal_decoder_dim=64,
            dropout=0.2,
            alias=model_name,
        )
    if model_name == "PatchTST":
        # NeuralForecast PatchTST is univariate and rejects historical exog.
        return PatchTST(
            **common,
            encoder_layers=2,
            n_heads=4,
            hidden_size=64,
            linear_hidden_size=128,
            patch_len=16,
            stride=8,
            learning_rate=5e-4,
            alias=model_name,
        )
    if model_name == "NHITS":
        return NHITS(
            **common,
            hist_exog_list=list(historical_exogenous),
            stack_types=["identity", "identity", "identity"],
            n_blocks=[1, 1, 1],
            mlp_units=[[256, 256], [256, 256], [256, 256]],
            n_pool_kernel_size=[4, 2, 1],
            n_freq_downsample=[4, 2, 1],
            learning_rate=5e-4,
            alias=model_name,
        )
    raise ValueError(f"Unsupported sequence model: {model_name}")


def _metric_rows(
    predictions: pd.DataFrame,
    model_name: str,
) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
    for horizon in DEEP_FORECAST_HORIZONS:
        subset = predictions[predictions["step"] == horizon]
        actual = subset["actual_price"].to_numpy()
        current = subset["current_price"].to_numpy()
        predicted = subset[model_name].to_numpy()
        persistence_rmse = float(
            np.sqrt(mean_squared_error(actual, current))
        )
        rmse = float(np.sqrt(mean_squared_error(actual, predicted)))
        rows.append(
            {
                "horizon": horizon,
                "model": model_name,
                "rmse": rmse,
                "mae": float(mean_absolute_error(actual, predicted)),
                "mape": float(
                    np.mean(np.abs((actual - predicted) / actual)) * 100.0
                ),
                "direction_accuracy": float(
                    np.mean(
                        np.sign(predicted - current)
                        == np.sign(actual - current)
                    )
                ),
                "persistence_rmse": persistence_rmse,
                "rmse_improvement_vs_persistence_pct": float(
                    100.0 * (persistence_rmse - rmse) / persistence_rmse
                ),
                "windows": len(subset),
            }
        )
    return rows


def benchmark_sequence_models(
    n_windows: int,
    max_steps: int,
    master_features: pd.DataFrame | None = None,
) -> SequenceBenchmarkResult:
    """Train and compare TiDE, PatchTST and N-HiTS on identical windows."""

    from neuralforecast import NeuralForecast

    sequence, neural_frame, used, excluded = _prepare_sequence_data(
        master_features
    )
    rolling_frames: list[pd.DataFrame] = []
    future_frames: list[pd.DataFrame] = []
    metric_rows: list[dict[str, float | int | str]] = []
    fitted_forecasters: dict[str, object] = {}
    training_seconds: dict[str, float] = {}
    log_price_by_ds = neural_frame.set_index("ds")["y"]

    for model_name in DEEP_FORECAST_MODELS:
        started = time.perf_counter()
        validation_forecaster = NeuralForecast(
            models=[_build_model(model_name, used, max_steps)],
            freq=1,
        )
        rolling = validation_forecaster.cross_validation(
            df=neural_frame,
            n_windows=n_windows,
            step_size=max(DEEP_FORECAST_HORIZONS),
            val_size=DEEP_FORECAST_VALIDATION_SIZE,
            refit=False,
            verbose=False,
        )
        rolling = rolling.sort_values(["cutoff", "ds"]).reset_index(drop=True)
        rolling["step"] = rolling.groupby(
            ["unique_id", "cutoff"]
        ).cumcount() + 1
        rolling["current_price"] = np.exp(
            rolling["cutoff"].map(log_price_by_ds)
        )
        rolling["actual_price"] = np.exp(rolling["y"])
        rolling[model_name] = np.exp(rolling[model_name])
        rolling_frames.append(
            rolling[
                [
                    "unique_id",
                    "ds",
                    "cutoff",
                    "step",
                    "current_price",
                    "actual_price",
                    model_name,
                ]
            ]
        )
        metric_rows.extend(_metric_rows(rolling, model_name))

        production_forecaster = NeuralForecast(
            models=[_build_model(model_name, used, max_steps)],
            freq=1,
        )
        production_forecaster.fit(
            df=neural_frame,
            val_size=DEEP_FORECAST_VALIDATION_SIZE,
            verbose=False,
        )
        future = production_forecaster.predict().reset_index()
        future[model_name] = np.exp(future[model_name])
        future_frames.append(future[["unique_id", "ds", model_name]])
        fitted_forecasters[model_name] = production_forecaster
        training_seconds[model_name] = time.perf_counter() - started

    rolling_predictions = rolling_frames[0]
    for frame in rolling_frames[1:]:
        rolling_predictions = rolling_predictions.merge(
            frame,
            on=[
                "unique_id",
                "ds",
                "cutoff",
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
            on=["unique_id", "ds"],
            how="inner",
        )
    future_predictions = future_predictions.sort_values("ds").reset_index(
        drop=True
    )
    future_predictions["step"] = np.arange(
        1,
        len(future_predictions) + 1,
    )
    future_predictions["as_of_date"] = sequence.index[-1]

    return SequenceBenchmarkResult(
        metrics=pd.DataFrame(metric_rows),
        rolling_predictions=rolling_predictions,
        future_predictions=future_predictions,
        fitted_forecasters=fitted_forecasters,
        training_seconds=training_seconds,
        used_exogenous_features=used,
        excluded_exogenous_features=excluded,
        sequence_rows=len(sequence),
        sequence_start_date=sequence.index[0],
        sequence_end_date=sequence.index[-1],
    )


__all__ = ["SequenceBenchmarkResult", "benchmark_sequence_models"]
