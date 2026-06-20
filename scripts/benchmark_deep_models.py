"""Run the production sequence-model benchmark without full ingestion."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import (
    DEEP_FORECAST_DEFAULT_MAX_STEPS,
    DEEP_FORECAST_DEFAULT_WINDOWS,
)
from src.modeling.sequence_forecast import benchmark_sequence_models

OUTPUT_DIR = PROJECT_ROOT / "data" / "predictions" / "sequence_benchmark"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Benchmark TiDE, PatchTST and N-HiTS on rolling windows",
    )
    parser.add_argument(
        "--n-windows",
        type=int,
        default=DEEP_FORECAST_DEFAULT_WINDOWS,
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=DEEP_FORECAST_DEFAULT_MAX_STEPS,
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = benchmark_sequence_models(
        n_windows=args.n_windows,
        max_steps=args.max_steps,
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    result.metrics.to_csv(OUTPUT_DIR / "metrics.csv", index=False)
    result.rolling_predictions.to_csv(
        OUTPUT_DIR / "rolling_predictions.csv",
        index=False,
    )
    result.future_predictions.to_csv(
        OUTPUT_DIR / "future_predictions.csv",
        index=False,
    )
    print(result.metrics.to_string(index=False))
    print(f"\nSequence rows: {result.sequence_rows}")
    print(
        "Sequence range: "
        f"{result.sequence_start_date.date()} -> "
        f"{result.sequence_end_date.date()}"
    )
    print(f"Used exogenous: {list(result.used_exogenous_features)}")
    print(f"Excluded exogenous: {list(result.excluded_exogenous_features)}")
    print(f"Saved: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
