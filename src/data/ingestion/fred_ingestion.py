"""
src/data/ingestion/fred_ingestion.py
======================================
Fetch FRED time series và upsert vào raw.fred_daily / raw.fred_monthly.

Functions:
    fetch_fred_series   : Fetch một FRED series theo ID.
    ingest_fred_daily   : Fetch FRED_DAILY_SERIES → upsert raw.fred_daily.
    ingest_fred_monthly : Fetch FRED_MONTHLY_SERIES → upsert raw.fred_monthly.
"""

from __future__ import annotations

import pandas as pd
import requests

from src.utils.config_loader import (
    DATA_START_DATE, FRED_API_KEY, FRED_KEY_VALID,
    FRED_DAILY_SERIES, FRED_MONTHLY_SERIES, PG_SCHEMA_RAW,
)
from src.utils.logging_config import get_logger
from src.data.storage.postgres_client import upsert_dataframe

logger = get_logger(__name__)
_FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


def fetch_fred_series(series_id: str, api_key: str = FRED_API_KEY, start: str = DATA_START_DATE) -> pd.DataFrame:
    """Fetch một FRED series, trả về DataFrame ['date', 'series_id', 'value']."""
    params = {
        "series_id": series_id, "api_key": api_key,
        "file_type": "json", "observation_start": start,
    }
    response = requests.get(_FRED_BASE_URL, params=params, timeout=30)
    response.raise_for_status()

    observations = response.json().get("observations", [])
    if not observations:
        return pd.DataFrame()

    df = pd.DataFrame(observations)[["date", "value"]].copy()
    df["date"]      = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["value"]     = pd.to_numeric(df["value"], errors="coerce")
    df["series_id"] = series_id

    df = df.dropna(subset=["date", "value"]).drop_duplicates(subset=["date", "series_id"], keep="last")
    return df[["date", "series_id", "value"]]


def ingest_fred_daily(series_map: dict[str, str] = FRED_DAILY_SERIES, start: str = DATA_START_DATE) -> dict[str, int]:
    """Fetch tất cả FRED daily series và upsert vào raw.fred_daily."""
    if not FRED_KEY_VALID:
        logger.error("FRED_API_KEY không hợp lệ — bỏ qua FRED daily")
        return {}

    results: dict[str, int] = {}
    for series_id in series_map:
        try:
            df = fetch_fred_series(series_id, start=start)
            if df.empty:
                results[series_id] = 0
                continue
            n = upsert_dataframe(df, table="fred_daily", schema=PG_SCHEMA_RAW, conflict_cols=["date", "series_id"])
            results[series_id] = n
        except Exception:
            logger.exception("Lỗi FRED daily", extra={"series_id": series_id})
            results[series_id] = -1

    logger.info("ingest_fred_daily done", extra={"total": sum(v for v in results.values() if v > 0)})
    return results


def ingest_fred_monthly(series_map: dict[str, str] = FRED_MONTHLY_SERIES, start: str = DATA_START_DATE) -> dict[str, int]:
    """Fetch tất cả FRED monthly series và upsert vào raw.fred_monthly."""
    if not FRED_KEY_VALID:
        logger.error("FRED_API_KEY không hợp lệ — bỏ qua FRED monthly")
        return {}

    results: dict[str, int] = {}
    for series_id in series_map:
        try:
            df = fetch_fred_series(series_id, start=start)
            if df.empty:
                results[series_id] = 0
                continue
            n = upsert_dataframe(df, table="fred_monthly", schema=PG_SCHEMA_RAW, conflict_cols=["date", "series_id"])
            results[series_id] = n
        except Exception:
            logger.exception("Lỗi FRED monthly", extra={"series_id": series_id})
            results[series_id] = -1

    logger.info("ingest_fred_monthly done", extra={"total": sum(v for v in results.values() if v > 0)})
    return results
