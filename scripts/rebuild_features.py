"""Rebuild staging and feature tables without re-downloading APIs."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipelines.ingestion import (
    populate_staging_daily_master,
    prepare_database_schema,
    run_cleaning,
    run_feature_engineering,
)


if __name__ == "__main__":
    prepare_database_schema()
    staging_rows = populate_staging_daily_master()
    run_cleaning()
    feature_rows = run_feature_engineering()
    print(f"staging.daily_master={staging_rows}")
    for table, rows in feature_rows.items():
        print(f"features.{table}={rows}")
