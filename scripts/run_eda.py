"""Command-line entrypoint for the EDA pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipelines.eda import run_eda_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run gold-price EDA")
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Print EDA summaries without opening plot windows",
    )
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    run_eda_pipeline(show_plots=not args.no_plots)
