"""
src/pipelines/environment_check.py
==================================
Environment and database readiness checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import pandas as pd
from sqlalchemy import text

from src.data.storage.postgres_client import get_engine
from src.utils.config_loader import (
    CFTC_PATH,
    DATA_END_DATE,
    DATA_START_DATE,
    EIA_KEY_VALID,
    EIA_PATH,
    FRED_KEY_VALID,
    FRED_PATH,
    FREEGOLD_PATH,
    PG_SCHEMA_FEATURES,
    PG_SCHEMA_FORECASTING,
    PG_SCHEMA_RAW,
    PG_SCHEMA_STAGING,
    SQL_DIR,
    PREDICTIONS_DIR,
    YFINANCE_PATH,
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


DEFAULT_REQUIRED_DIRECTORIES: tuple[Path, ...] = (
    FREEGOLD_PATH,
    YFINANCE_PATH,
    FRED_PATH,
    EIA_PATH,
    CFTC_PATH,
    PREDICTIONS_DIR,
)

DEFAULT_TABLES_TO_CHECK: tuple[tuple[str, str], ...] = (
    (PG_SCHEMA_RAW, "gold_prices"),
    (PG_SCHEMA_RAW, "yfinance_daily"),
    (PG_SCHEMA_RAW, "fred_daily"),
    (PG_SCHEMA_RAW, "fred_monthly"),
    (PG_SCHEMA_RAW, "eia_oil"),
    (PG_SCHEMA_RAW, "cftc_gold_positioning"),
    (PG_SCHEMA_STAGING, "daily_master"),
    (PG_SCHEMA_FEATURES, "price_indicators"),
    (PG_SCHEMA_FEATURES, "momentum_indicators"),
    (PG_SCHEMA_FEATURES, "trend_indicators"),
    (PG_SCHEMA_FEATURES, "macro_features"),
    (PG_SCHEMA_FEATURES, "ratio_features"),
    (PG_SCHEMA_FEATURES, "sliding_windows"),
    (PG_SCHEMA_FEATURES, "target_labels"),
    (PG_SCHEMA_FEATURES, "ewma_features"),
    (PG_SCHEMA_FEATURES, "seasonality_features"),
    (PG_SCHEMA_FEATURES, "market_driver_features"),
    (PG_SCHEMA_FEATURES, "master_features"),
    (PG_SCHEMA_FORECASTING, "model_runs"),
    (PG_SCHEMA_FORECASTING, "model_candidates"),
    (PG_SCHEMA_FORECASTING, "model_metrics"),
    (PG_SCHEMA_FORECASTING, "open_predictions"),
    (PG_SCHEMA_FORECASTING, "stage_metrics"),
    (PG_SCHEMA_FORECASTING, "resource_metrics"),
)


@dataclass(frozen=True)
class PostgresConnectionCheck:
    """Result of the PostgreSQL connectivity check."""

    connected: bool
    version: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class EnvironmentCheckReport:
    """Structured result for the environment check pipeline."""

    project_root: Path
    data_start_date: str
    data_end_date: str | None
    fred_key_valid: bool
    eia_key_valid: bool
    postgres: PostgresConnectionCheck
    database_status: pd.DataFrame
    created_directories: tuple[Path, ...]


def check_postgres_connection() -> PostgresConnectionCheck:
    """Check whether PostgreSQL is reachable and return server version."""
    try:
        engine = get_engine()
        with engine.connect() as connection:
            version = connection.execute(text("SELECT version()")).scalar()

        version_text = str(version) if version is not None else None
        return PostgresConnectionCheck(connected=True, version=version_text)
    except Exception as exc:  # pragma: no cover - runtime/environment dependent
        logger.exception("PostgreSQL connection failed")
        return PostgresConnectionCheck(connected=False, error=str(exc))


def build_database_status_frame(
    tables_to_check: Sequence[tuple[str, str]] = DEFAULT_TABLES_TO_CHECK,
) -> pd.DataFrame:
    """Build table existence and row-count diagnostics."""
    rows: list[dict[str, object]] = []

    engine = get_engine()
    with engine.connect() as connection:
        for schema, table in tables_to_check:
            exists = bool(
                connection.execute(
                    text(
                        """
                        SELECT EXISTS (
                            SELECT 1
                            FROM information_schema.tables
                            WHERE table_schema = :schema
                              AND table_name = :table
                        )
                        """
                    ),
                    {"schema": schema, "table": table},
                ).scalar()
            )
            row_count = (
                int(
                    connection.execute(
                        text(f'SELECT COUNT(*) FROM "{schema}"."{table}"')
                    ).scalar()
                )
                if exists
                else 0
            )
            status = (
                "OK"
                if exists and row_count > 0
                else ("EMPTY" if exists else "NOT FOUND")
            )
            rows.append(
                {
                    "schema.table": f"{schema}.{table}",
                    "rows": row_count,
                    "status": status,
                }
            )

    return pd.DataFrame(rows)


def ensure_required_directories(
    directories: Sequence[Path] = DEFAULT_REQUIRED_DIRECTORIES,
) -> tuple[Path, ...]:
    """Create source-specific raw incoming directories if they do not exist."""
    created_directories: list[Path] = []
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        created_directories.append(directory)
    return tuple(created_directories)


def render_environment_check_report(report: EnvironmentCheckReport) -> None:
    """Print a human-readable summary of the environment check."""
    print(f"[OK]  Project root: {report.project_root}")
    print(f"[INFO] Data range     : {report.data_start_date} -> {report.data_end_date or 'today'}")
    print(
        f"[INFO] FRED API key   : {'VALID' if report.fred_key_valid else 'MISSING - set FRED_API_KEY in .env'}"
    )
    print(
        f"[INFO] EIA API key    : {'VALID' if report.eia_key_valid else 'MISSING - will use yfinance fallback'}"
    )
    print(
        f"[INFO] PG Schemas     : {PG_SCHEMA_RAW}, {PG_SCHEMA_STAGING}, "
        f"{PG_SCHEMA_FEATURES}, {PG_SCHEMA_FORECASTING}"
    )
    print(f"[INFO] SQL Dir        : {SQL_DIR}")

    if report.postgres.connected:
        print("[OK]  PostgreSQL connected")
        if report.postgres.version:
            print(f"      Version: {report.postgres.version[:60]}...")
    else:
        print(f"[ERR] PostgreSQL connection FAILED: {report.postgres.error}")
        print("      Check DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME in .env")

    if not report.database_status.empty:
        print(report.database_status.to_string(index=False))
    else:
        print("[WARN] No database tables configured for checking")

    for directory in report.created_directories:
        print(f"[OK]  Dir ready: {directory}")

    print("\n[DONE] Environment check completed")


def run_environment_check(
    tables_to_check: Sequence[tuple[str, str]] = DEFAULT_TABLES_TO_CHECK,
    required_directories: Sequence[Path] = DEFAULT_REQUIRED_DIRECTORIES,
) -> EnvironmentCheckReport:
    """Run the full environment check flow and return a structured report."""
    postgres_check = check_postgres_connection()
    database_status = build_database_status_frame(tables_to_check=tables_to_check)
    created_directories = ensure_required_directories(required_directories)

    report = EnvironmentCheckReport(
        project_root=Path(__file__).resolve().parents[2],
        data_start_date=DATA_START_DATE,
        data_end_date=DATA_END_DATE,
        fred_key_valid=FRED_KEY_VALID,
        eia_key_valid=EIA_KEY_VALID,
        postgres=postgres_check,
        database_status=database_status,
        created_directories=created_directories,
    )
    render_environment_check_report(report)
    return report


__all__ = [
    "DEFAULT_REQUIRED_DIRECTORIES",
    "DEFAULT_TABLES_TO_CHECK",
    "EnvironmentCheckReport",
    "PostgresConnectionCheck",
    "build_database_status_frame",
    "check_postgres_connection",
    "ensure_required_directories",
    "render_environment_check_report",
    "run_environment_check",
]
