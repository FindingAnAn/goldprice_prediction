"""
src/pipelines/ingestion.py
==========================
High-level ingestion pipeline for the Gold Time Prediction project.

This module orchestrates the existing ingestion, cleaning, and feature
engineering helpers so the notebook logic can be reused from a script or test.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.data.ingestion.eia_ingestion import ingest_eia_with_fallback
from src.data.ingestion.fred_ingestion import ingest_fred_daily, ingest_fred_monthly
from src.data.ingestion.freegold_ingestion import ingest_gold_prices
from src.data.ingestion.yfinance_ingestion import ingest_yfinance_all
from src.data.preprocessing.cleaning import run_cleaning_pipeline
from src.data.storage.postgres_client import (
    execute_sql_file,
    get_engine,
    get_row_count,
    run_feature_pipeline,
    run_schema_pipeline,
)
from src.utils.config_loader import DATA_END_DATE, DATA_START_DATE, SQL_DIR
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

DEFAULT_FEATURE_TABLES: tuple[str, ...] = (
    "price_indicators",
    "momentum_indicators",
    "trend_indicators",
    "macro_features",
    "ratio_features",
    "sliding_windows",
    "target_labels",
    "ewma_features",
    "master_features",
)


@dataclass(frozen=True)
class IngestionReport:
    """Structured result of the ingestion pipeline."""

    gold_rows_upserted: int
    yfinance_rows: dict[str, int]
    fred_daily_rows: dict[str, int]
    fred_monthly_rows: dict[str, int]
    eia_rows: dict[str, int]
    staging_rows: int
    feature_rows: dict[str, int]
    master_feature_sample: pd.DataFrame
    target_label_sample: pd.DataFrame


def prepare_database_schema() -> None:
    """Create raw, staging, and features schemas and tables."""
    run_schema_pipeline()


def ingest_raw_sources(
    start: str = DATA_START_DATE,
    end: str | None = DATA_END_DATE,
) -> tuple[int, dict[str, int], dict[str, int], dict[str, int], dict[str, int]]:
    """Run the raw source ingestion steps."""
    gold_rows = ingest_gold_prices(start=start, end=end)
    yfinance_rows = ingest_yfinance_all(start=start, end=end)
    fred_daily_rows = ingest_fred_daily(start=start, end=end)
    fred_monthly_rows = ingest_fred_monthly(start=start, end=end)
    eia_rows = ingest_eia_with_fallback(start=start, end=end)
    return gold_rows, yfinance_rows, fred_daily_rows, fred_monthly_rows, eia_rows


def populate_staging_daily_master() -> int:
    """Populate staging.daily_master using the SQL pipeline."""
    execute_sql_file(SQL_DIR / "schema" / "00_populate_staging.sql")
    return get_row_count("staging", "daily_master")


def run_cleaning(max_gap_days: int = 3, z_threshold: float = 5.0) -> None:
    """Run the PostgreSQL cleaning pipeline."""
    run_cleaning_pipeline(max_gap_days=max_gap_days, z_threshold=z_threshold)


def run_feature_engineering() -> dict[str, int]:
    """Run SQL feature engineering and return row counts."""
    run_feature_pipeline()
    return {table: get_row_count("features", table) for table in DEFAULT_FEATURE_TABLES}


def load_master_feature_sample(limit: int = 10) -> pd.DataFrame:
    """Load a sample from features.master_features for verification.

    Note: gold_close and gold_open are intentionally absent from master_features
    (they are reserved as prediction targets in features.target_labels).
    """
    engine = get_engine()
    with engine.connect() as connection:
        return pd.read_sql(
            f"""
            SELECT date, gold_high, gold_low, gold_volume,
                   sma_20, rsi_14, macd, adx_14,
                   dxy_close, gold_silver_ratio, real_yield,
                   gold_pct_chg_21d, ewma_30d, price_vs_ewma_30d
            FROM features.master_features
            ORDER BY date DESC
            LIMIT {limit}
            """,
            connection,
            parse_dates=["date"],
            index_col="date",
        )


def load_target_label_sample(limit: int = 5) -> pd.DataFrame:
    """Load a sample from features.target_labels for verification."""
    engine = get_engine()
    with engine.connect() as connection:
        return pd.read_sql(
            f"""
            SELECT date, next_1_day_price, next_7_day_price, next_30_day_price
            FROM features.target_labels
            ORDER BY date DESC
            LIMIT {limit}
            """,
            connection,
            parse_dates=["date"],
            index_col="date",
        )


def render_ingestion_report(report: IngestionReport) -> None:
    """Print a notebook-style summary of the ingestion pipeline."""
    print("[OK] Ingestion pipeline completed")
    print(f"[INFO] Gold rows upserted : {report.gold_rows_upserted}")
    print(f"[INFO] staging.daily_master: {report.staging_rows:,} rows")

    print("\n[INFO] yfinance ingestion")
    for ticker, rows in report.yfinance_rows.items():
        print(f"  - {ticker}: {rows}")

    print("\n[INFO] FRED daily ingestion")
    for series_id, rows in report.fred_daily_rows.items():
        print(f"  - {series_id}: {rows}")

    print("\n[INFO] FRED monthly ingestion")
    for series_id, rows in report.fred_monthly_rows.items():
        print(f"  - {series_id}: {rows}")

    print("\n[INFO] EIA ingestion")
    for series_id, rows in report.eia_rows.items():
        print(f"  - {series_id}: {rows}")

    print("\n[INFO] Feature rows")
    for table, rows in report.feature_rows.items():
        print(f"  - features.{table}: {rows:,}")

    print("\n[INFO] Sample from features.master_features")
    print(report.master_feature_sample.to_string())

    print("\n[INFO] Sample from features.target_labels")
    print(report.target_label_sample.to_string())


def run_ingestion_pipeline(
    start: str = DATA_START_DATE,
    end: str | None = DATA_END_DATE,
    max_gap_days: int = 3,
    z_threshold: float = 5.0,
) -> IngestionReport:
    """Run the end-to-end ingestion pipeline."""
    logger.info("Starting ingestion pipeline", extra={"start": start, "end": end})

    prepare_database_schema()
    gold_rows, yfinance_rows, fred_daily_rows, fred_monthly_rows, eia_rows = ingest_raw_sources(
        start=start,
        end=end,
    )
    staging_rows = populate_staging_daily_master()
    run_cleaning(max_gap_days=max_gap_days, z_threshold=z_threshold)
    feature_rows = run_feature_engineering()
    master_feature_sample = load_master_feature_sample()
    target_label_sample = load_target_label_sample()

    report = IngestionReport(
        gold_rows_upserted=gold_rows,
        yfinance_rows=yfinance_rows,
        fred_daily_rows=fred_daily_rows,
        fred_monthly_rows=fred_monthly_rows,
        eia_rows=eia_rows,
        staging_rows=staging_rows,
        feature_rows=feature_rows,
        master_feature_sample=master_feature_sample,
        target_label_sample=target_label_sample,
    )
    render_ingestion_report(report)
    return report


__all__ = [
    "DEFAULT_FEATURE_TABLES",
    "IngestionReport",
    "ingest_raw_sources",
    "load_master_feature_sample",
    "load_target_label_sample",
    "populate_staging_daily_master",
    "prepare_database_schema",
    "render_ingestion_report",
    "run_cleaning",
    "run_feature_engineering",
    "run_ingestion_pipeline",
]
