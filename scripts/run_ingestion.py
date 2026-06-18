"""Command-line entrypoint for the ingestion pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipelines.ingestion import run_ingestion_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run gold-price ingestion")
    parser.add_argument("--start", default="2000-01-01")
    parser.add_argument(
        "--end",
        default=None,
        help="Inclusive end date YYYY-MM-DD; default fetches latest available",
    )
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    run_ingestion_pipeline(start=args.start, end=args.end)
