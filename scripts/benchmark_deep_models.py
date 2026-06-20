"""Benchmark TiDE, PatchTST and optionally TabPFN-TS on rolling time windows."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipelines.eda_data import load_master_features

OUTPUT_DIR = PROJECT_ROOT / "data" / "predictions" / "deep_models"
EVALUATION_HORIZONS = (5, 7, 10, 21)


def _metric_rows(
    predictions: pd.DataFrame,
    model_columns: list[str],
) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for horizon in EVALUATION_HORIZONS:
        subset = predictions[predictions["step"] == horizon]
        actual = subset["actual_price"].to_numpy()
        current = subset["current_price"].to_numpy()
        persistence_rmse = float(
            np.sqrt(mean_squared_error(actual, current))
        )
        for model_column in model_columns:
            predicted = subset[model_column].to_numpy()
            direction_accuracy = (
                float("nan")
                if np.allclose(predicted, current)
                else float(
                    np.mean(
                        np.sign(predicted - current)
                        == np.sign(actual - current)
                    )
                )
            )
            rmse = float(np.sqrt(mean_squared_error(actual, predicted)))
            rows.append(
                {
                    "horizon": horizon,
                    "model": model_column,
                    "rmse": rmse,
                    "mae": float(mean_absolute_error(actual, predicted)),
                    "mape": float(
                        np.mean(np.abs((actual - predicted) / actual)) * 100.0
                    ),
                    "direction_accuracy": direction_accuracy,
                    "persistence_rmse": persistence_rmse,
                    "rmse_improvement_vs_persistence_pct": float(
                        100.0 * (persistence_rmse - rmse) / persistence_rmse
                    ),
                    "windows": len(subset),
                }
            )
    return pd.DataFrame(rows)


def benchmark_neuralforecast(
    n_windows: int = 12,
    max_steps: int = 200,
    architectures: tuple[str, ...] = ("tide", "patchtst"),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run CPU-oriented TiDE and PatchTST rolling evaluation."""

    from neuralforecast import NeuralForecast
    from neuralforecast.models import PatchTST, TiDE

    gold = load_master_features()[["gold_close"]].dropna().sort_index()
    series = pd.DataFrame(
        {
            "unique_id": "gold",
            "ds": np.arange(len(gold), dtype=np.int64),
            "y": np.log(gold["gold_close"].to_numpy()),
        }
    )

    models = []
    if "tide" in architectures:
        models.append(TiDE(
            h=max(EVALUATION_HORIZONS),
            input_size=252,
            hidden_size=128,
            decoder_output_dim=32,
            temporal_decoder_dim=64,
            dropout=0.2,
            scaler_type="robust",
            max_steps=max_steps,
            val_check_steps=25,
            early_stop_patience_steps=3,
            random_seed=42,
            alias="TiDE",
            enable_progress_bar=False,
            logger=False,
        ))
    if "patchtst" in architectures:
        models.append(PatchTST(
            h=max(EVALUATION_HORIZONS),
            input_size=252,
            encoder_layers=2,
            n_heads=4,
            hidden_size=64,
            linear_hidden_size=128,
            patch_len=16,
            stride=8,
            scaler_type="robust",
            learning_rate=5e-4,
            max_steps=max_steps,
            val_check_steps=25,
            early_stop_patience_steps=3,
            random_seed=42,
            alias="PatchTST",
            enable_progress_bar=False,
            logger=False,
        ))
    forecast = NeuralForecast(models=models, freq=1)
    cv = forecast.cross_validation(
        df=series,
        n_windows=n_windows,
        step_size=max(EVALUATION_HORIZONS),
        val_size=63,
        refit=False,
        verbose=False,
    )
    cv = cv.sort_values(["cutoff", "ds"]).reset_index(drop=True)
    cv["step"] = cv.groupby(["unique_id", "cutoff"]).cumcount() + 1
    log_price_by_ds = series.set_index("ds")["y"]
    cv["current_price"] = np.exp(cv["cutoff"].map(log_price_by_ds))
    cv["actual_price"] = np.exp(cv["y"])
    model_columns = [
        alias
        for key, alias in (("tide", "TiDE"), ("patchtst", "PatchTST"))
        if key in architectures
    ]
    for model_column in model_columns:
        cv[model_column] = np.exp(cv[model_column])

    metrics = _metric_rows(cv, model_columns)
    return metrics, cv


def benchmark_tabpfn_ts(
    n_windows: int = 4,
    mode: str = "local",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run TabPFN-TS when its checkpoint/client authentication is available."""

    from tabpfn_time_series import TabPFNMode, TabPFNTSPipeline

    gold = load_master_features()[["gold_close"]].dropna().sort_index()
    mode_value = TabPFNMode.LOCAL if mode == "local" else TabPFNMode.CLIENT
    pipeline = TabPFNTSPipeline(
        max_context_length=2048,
        tabpfn_mode=mode_value,
    )
    h = max(EVALUATION_HORIZONS)
    cutoff_positions = [
        len(gold) - h * window - 1
        for window in range(n_windows, 0, -1)
    ]
    outputs: list[pd.DataFrame] = []
    for window_id, cutoff_position in enumerate(cutoff_positions):
        context = gold.iloc[: cutoff_position + 1].reset_index()
        context_df = pd.DataFrame(
            {
                "item_id": "gold",
                "timestamp": context["date"],
                "target": np.log(context["gold_close"]),
            }
        )
        future_dates = gold.index[
            cutoff_position + 1 : cutoff_position + h + 1
        ]
        future_df = pd.DataFrame(
            {
                "item_id": "gold",
                "timestamp": future_dates,
            }
        )
        try:
            prediction = pipeline.predict_df(
                context_df,
                future_df=future_df,
            ).reset_index()
        except OSError as exc:
            raise RuntimeError(
                "TabPFN-TS local weights require one-time Prior Labs license "
                "acceptance. Visit https://ux.priorlabs.ai/account/licenses, "
                "set the provided API key, then rerun this command."
            ) from exc
        median_column = 0.5 if 0.5 in prediction.columns else "0.5"
        predicted_price = np.exp(prediction[median_column].to_numpy())
        actual = gold.iloc[
            cutoff_position + 1 : cutoff_position + h + 1
        ]["gold_close"].to_numpy()
        current = float(gold.iloc[cutoff_position]["gold_close"])
        outputs.append(
            pd.DataFrame(
                {
                    "window": window_id,
                    "step": np.arange(1, h + 1),
                    "actual_price": actual,
                    "current_price": current,
                    "TabPFN-TS": predicted_price,
                }
            )
        )

    predictions = pd.concat(outputs, ignore_index=True)
    metrics = _metric_rows(predictions, ["TabPFN-TS"])
    return metrics, predictions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--models",
        nargs="+",
        choices=("neuralforecast", "tabpfn-ts"),
        default=("neuralforecast",),
    )
    parser.add_argument("--n-windows", type=int, default=12)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument(
        "--architectures",
        nargs="+",
        choices=("tide", "patchtst"),
        default=("tide", "patchtst"),
    )
    parser.add_argument(
        "--tabpfn-mode",
        choices=("local", "client"),
        default="local",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    metric_frames: list[pd.DataFrame] = []

    if "neuralforecast" in args.models:
        metrics, predictions = benchmark_neuralforecast(
            n_windows=args.n_windows,
            max_steps=args.max_steps,
            architectures=tuple(args.architectures),
        )
        metrics["benchmark"] = "rolling_fixed_model"
        metric_frames.append(metrics)
        predictions.to_csv(
            OUTPUT_DIR / "neuralforecast_predictions.csv",
            index=False,
        )

    if "tabpfn-ts" in args.models:
        metrics, predictions = benchmark_tabpfn_ts(
            n_windows=min(args.n_windows, 4),
            mode=args.tabpfn_mode,
        )
        metrics["benchmark"] = "rolling_zero_shot"
        metric_frames.append(metrics)
        predictions.to_csv(
            OUTPUT_DIR / "tabpfn_ts_predictions.csv",
            index=False,
        )

    result = pd.concat(metric_frames, ignore_index=True)
    metrics_path = OUTPUT_DIR / "deep_model_metrics.csv"
    if metrics_path.exists():
        previous = pd.read_csv(metrics_path)
        refreshed_models = set(result["model"])
        previous = previous[~previous["model"].isin(refreshed_models)]
        result = pd.concat([previous, result], ignore_index=True)
    result.to_csv(metrics_path, index=False)
    print(result.to_string(index=False))
    print(f"\nSaved: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
