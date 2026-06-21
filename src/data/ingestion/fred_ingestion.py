"""Fetch FRED series and upsert them into PostgreSQL."""

from __future__ import annotations

from io import StringIO

import pandas as pd
import requests

from src.data.storage.postgres_client import upsert_dataframe
from src.utils.config_loader import (
    DATA_END_DATE,
    DATA_START_DATE,
    FRED_API_KEY,
    FRED_DAILY_SERIES,
    FRED_KEY_VALID,
    FRED_MONTHLY_SERIES,
    PG_SCHEMA_RAW,
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)
_FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
_FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"


def fetch_fred_series(
    series_id: str,
    api_key: str = FRED_API_KEY,
    start: str = DATA_START_DATE,
    end: str | None = DATA_END_DATE,
) -> pd.DataFrame:
    """Fetch one FRED series using JSON API or the public CSV fallback."""

    if FRED_KEY_VALID and api_key:
        params = {
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
            "observation_start": start,
        }
        if end is not None:
            params["observation_end"] = end
        response = requests.get(_FRED_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        observations = response.json().get("observations", [])
        if not observations:
            return pd.DataFrame()
        df = pd.DataFrame(observations)[["date", "value"]].copy()
    else:
        params = {"id": series_id, "cosd": start}
        if end is not None:
            params["coed"] = end
        response = requests.get(_FRED_CSV_URL, params=params, timeout=30)
        response.raise_for_status()
        csv_df = pd.read_csv(StringIO(response.text))
        if csv_df.empty or len(csv_df.columns) < 2:
            return pd.DataFrame()
        df = csv_df.iloc[:, :2].copy()
        df.columns = ["date", "value"]

    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["series_id"] = series_id
    df = df.dropna(subset=["date", "value"]).drop_duplicates(
        subset=["date", "series_id"],
        keep="last",
    )
    return df[["date", "series_id", "value"]]


def ingest_fred_daily(
    series_map: dict[str, str] = FRED_DAILY_SERIES,
    start: str = DATA_START_DATE,
    end: str | None = DATA_END_DATE,
) -> dict[str, int]:
    """Fetch all configured daily FRED series and upsert them."""

    results: dict[str, int] = {}
    for series_id in series_map:
        try:
            df = fetch_fred_series(series_id, start=start, end=end)
            if df.empty:
                results[series_id] = 0
                continue
            results[series_id] = upsert_dataframe(
                df,
                table="fred_daily",
                schema=PG_SCHEMA_RAW,
                conflict_cols=["date", "series_id"],
            )
        except Exception:
            logger.exception(
                "FRED daily ingestion failed",
                extra={"series_id": series_id},
            )
            results[series_id] = -1

    logger.info(
        "ingest_fred_daily done",
        extra={"total": sum(value for value in results.values() if value > 0)},
    )
    return results


def ingest_fred_monthly(
    series_map: dict[str, str] = FRED_MONTHLY_SERIES,
    start: str = DATA_START_DATE,
    end: str | None = DATA_END_DATE,
) -> dict[str, int]:
    """Fetch all configured monthly FRED series and upsert them."""

    results: dict[str, int] = {}
    for series_id in series_map:
        try:
            df = fetch_fred_series(series_id, start=start, end=end)
            if df.empty:
                results[series_id] = 0
                continue
            results[series_id] = upsert_dataframe(
                df,
                table="fred_monthly",
                schema=PG_SCHEMA_RAW,
                conflict_cols=["date", "series_id"],
            )
        except Exception:
            logger.exception(
                "FRED monthly ingestion failed",
                extra={"series_id": series_id},
            )
            results[series_id] = -1

    logger.info(
        "ingest_fred_monthly done",
        extra={"total": sum(value for value in results.values() if value > 0)},
    )
    return results
