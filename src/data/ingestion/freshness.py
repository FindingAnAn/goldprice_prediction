"""Freshness diagnostics for external APIs and PostgreSQL raw tables."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import text

from src.data.ingestion.cftc_ingestion import fetch_cftc_current_positioning
from src.data.ingestion.eia_ingestion import fetch_eia_series
from src.data.ingestion.fred_ingestion import fetch_fred_series
from src.data.ingestion.freegold_ingestion import fetch_freegoldapi
from src.data.ingestion.yfinance_ingestion import fetch_yfinance_ohlcv
from src.data.storage.postgres_client import get_engine
from src.utils.config_loader import (
    EIA_KEY_VALID,
    EIA_SERIES,
    FRED_DAILY_SERIES,
    FRED_MONTHLY_SERIES,
    DATA_START_DATE,
    YFINANCE_OHLCV_TICKERS,
)


@dataclass(frozen=True)
class FreshnessRecord:
    source: str
    item: str
    latest_date: date | None
    status: str
    detail: str = ""


def _latest_date(frame: object) -> date | None:
    if getattr(frame, "empty", True):
        return None
    value = frame["date"].max()
    return value if isinstance(value, date) else value.date()


def collect_api_freshness(
    reference_date: date | None = None,
) -> list[FreshnessRecord]:
    """Call configured APIs and return their latest available observation."""

    reference_date = reference_date or date.today()
    daily_start = (reference_date - timedelta(days=45)).isoformat()
    monthly_start = (reference_date - timedelta(days=550)).isoformat()
    records: list[FreshnessRecord] = []

    try:
        frame = fetch_freegoldapi(start=DATA_START_DATE)
        records.append(
            FreshnessRecord(
                "FreeGoldAPI",
                "latest.csv",
                _latest_date(frame),
                "fallback_only",
                "Historical fallback; Yahoo GC=F is the current primary source.",
            )
        )
    except Exception as exc:
        records.append(FreshnessRecord("FreeGoldAPI", "latest.csv", None, "error", str(exc)))

    for ticker in YFINANCE_OHLCV_TICKERS:
        try:
            frame = fetch_yfinance_ohlcv(ticker, start=daily_start)
            records.append(
                FreshnessRecord("Yahoo Finance", ticker, _latest_date(frame), "ok")
            )
        except Exception as exc:
            records.append(FreshnessRecord("Yahoo Finance", ticker, None, "error", str(exc)))

    for series_id in FRED_DAILY_SERIES:
        try:
            frame = fetch_fred_series(series_id, start=daily_start)
            records.append(FreshnessRecord("FRED daily", series_id, _latest_date(frame), "ok"))
        except Exception as exc:
            records.append(FreshnessRecord("FRED daily", series_id, None, "error", str(exc)))

    for series_id in FRED_MONTHLY_SERIES:
        try:
            frame = fetch_fred_series(series_id, start=monthly_start)
            records.append(FreshnessRecord("FRED monthly", series_id, _latest_date(frame), "ok"))
        except Exception as exc:
            records.append(FreshnessRecord("FRED monthly", series_id, None, "error", str(exc)))

    if EIA_KEY_VALID:
        for series_id, column_name in EIA_SERIES.items():
            try:
                frame = fetch_eia_series(series_id, column_name, start=daily_start)
                records.append(FreshnessRecord("EIA", series_id, _latest_date(frame), "ok"))
            except Exception as exc:
                records.append(FreshnessRecord("EIA", series_id, None, "error", str(exc)))
    else:
        for series_id in EIA_SERIES:
            records.append(
                FreshnessRecord(
                    "EIA",
                    series_id,
                    None,
                    "fallback",
                    "EIA_API_KEY missing; pipeline uses CL=F/BZ=F.",
                )
            )

    try:
        frame = fetch_cftc_current_positioning()
        latest = frame["available_date"].max() if not frame.empty else None
        records.append(
            FreshnessRecord(
                "CFTC",
                "Gold disaggregated",
                latest,
                "ok" if latest else "empty",
                "available_date = report Tuesday + 3 calendar days",
            )
        )
    except Exception as exc:
        records.append(
            FreshnessRecord(
                "CFTC",
                "Gold disaggregated",
                None,
                "error",
                str(exc),
            )
        )

    return records


def collect_database_freshness() -> list[FreshnessRecord]:
    """Return latest stored dates; report unavailable when PostgreSQL is offline."""

    queries = {
        ("PostgreSQL", "raw.gold_prices"): "SELECT MAX(date) FROM raw.gold_prices",
        ("PostgreSQL", "raw.yfinance_daily"): "SELECT MAX(date) FROM raw.yfinance_daily",
        ("PostgreSQL", "raw.fred_daily"): "SELECT MAX(date) FROM raw.fred_daily",
        ("PostgreSQL", "raw.fred_monthly"): "SELECT MAX(date) FROM raw.fred_monthly",
        ("PostgreSQL", "raw.eia_oil"): "SELECT MAX(date) FROM raw.eia_oil",
        ("PostgreSQL", "raw.cftc_gold_positioning"): (
            "SELECT MAX(available_date) FROM raw.cftc_gold_positioning"
        ),
        ("PostgreSQL", "staging.daily_master"): "SELECT MAX(date) FROM staging.daily_master",
        ("PostgreSQL", "features.master_features"): "SELECT MAX(date) FROM features.master_features",
        ("PostgreSQL", "forecasting.model_runs"): (
            "SELECT MAX(started_at)::date FROM forecasting.model_runs"
        ),
    }
    try:
        engine = get_engine()
        with engine.connect() as connection:
            return [
                FreshnessRecord(source, item, connection.execute(text(query)).scalar(), "ok")
                for (source, item), query in queries.items()
            ]
    except Exception as exc:
        return [FreshnessRecord("PostgreSQL", "connection", None, "unavailable", str(exc))]


__all__ = [
    "FreshnessRecord",
    "collect_api_freshness",
    "collect_database_freshness",
]
