"""
src/data/ingestion/eia_ingestion.py
=====================================
Fetch EIA crude oil prices và upsert vào raw.eia_oil.
Tự động fallback sang yfinance nếu EIA API lỗi.

Functions:
    fetch_eia_series        : Fetch một EIA series (paginated).
    ingest_eia_with_fallback: Fetch WTI + Brent → upsert raw.eia_oil.
"""

from __future__ import annotations

import pandas as pd
import requests
import yfinance as yf

from src.utils.config_loader import (
    DATA_END_DATE, DATA_START_DATE, EIA_API_KEY, EIA_KEY_VALID,
    EIA_BASE_URL, EIA_SERIES, EIA_YFINANCE_FALLBACK, PG_SCHEMA_RAW,
)
from src.utils.logging_config import get_logger
from src.data.storage.postgres_client import upsert_dataframe

logger = get_logger(__name__)


def fetch_eia_series(
    series_id: str,
    col_name: str,
    api_key: str = EIA_API_KEY,
    start: str = DATA_START_DATE,
    end: str | None = DATA_END_DATE,
) -> pd.DataFrame:
    """Fetch một EIA series với pagination, trả về ['date', 'series_id', 'value']."""
    params: dict = {
        "api_key": api_key, "data[]": "value",
        "facets[series][]": series_id, "frequency": "daily",
        "start": start, "sort[0][column]": "period",
        "sort[0][direction]": "asc", "length": 5000,
    }
    if end is not None:
        params["end"] = end
    all_rows: list[dict] = []
    offset = 0

    while True:
        params["offset"] = offset
        response = requests.get(EIA_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()

        if "error" in payload:
            raise ValueError(f"EIA API error for {series_id}: {payload['error']}")

        rows = payload.get("response", {}).get("data", [])
        if not rows:
            break
        all_rows.extend(rows)
        if len(rows) < 5000:
            break
        offset += 5000

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)[["period", "value"]].copy()
    df.columns = pd.Index(["date", "value"])
    df["date"]      = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["value"]     = pd.to_numeric(df["value"], errors="coerce")
    df["series_id"] = series_id
    df = df.dropna(subset=["date", "value"]).drop_duplicates(subset=["date", "series_id"])
    return df[["date", "series_id", "value"]]


def _fetch_from_yfinance(
    symbol: str,
    series_id: str,
    start: str,
    end: str | None,
) -> pd.DataFrame:
    """Fallback: fetch close price từ yfinance, format giống EIA long table."""
    try:
        from src.data.ingestion.yfinance_ingestion import _exclusive_yfinance_end

        raw = yf.download(
            symbol,
            start=start,
            end=_exclusive_yfinance_end(end),
            auto_adjust=True,
            progress=False,
        )
        if raw.empty:
            return pd.DataFrame()
        close = raw["Close"].squeeze()
        df = pd.DataFrame({
            "date":      close.index.date,
            "series_id": series_id,
            "value":     close.values,
        })
        df = df.dropna(subset=["value"]).drop_duplicates(subset=["date", "series_id"])
        logger.info("yfinance fallback OK", extra={"symbol": symbol, "rows": len(df)})
        return df
    except Exception:
        logger.exception("yfinance fallback lỗi", extra={"symbol": symbol})
        return pd.DataFrame()


def ingest_eia_with_fallback(
    series_map: dict[str, str] = EIA_SERIES,
    fallback_map: dict[str, str] = EIA_YFINANCE_FALLBACK,
    start: str = DATA_START_DATE,
    end: str | None = DATA_END_DATE,
) -> dict[str, int]:
    """Fetch WTI + Brent từ EIA (fallback yfinance) → upsert raw.eia_oil.

    Returns:
        Dict mapping series_id → số dòng upserted.
    """
    results: dict[str, int] = {}

    for series_id, col_name in series_map.items():
        df = pd.DataFrame()

        if EIA_KEY_VALID:
            try:
                df = fetch_eia_series(
                    series_id,
                    col_name,
                    start=start,
                    end=end,
                )
                logger.info("EIA series fetched", extra={"series_id": series_id, "rows": len(df)})
            except Exception:
                logger.exception("EIA series lỗi, thử yfinance fallback", extra={"series_id": series_id})

        if df.empty:
            yf_symbol = fallback_map.get(series_id)
            if yf_symbol:
                df = _fetch_from_yfinance(yf_symbol, series_id, start, end)

        if df.empty:
            logger.error("Không có data cho oil series", extra={"series_id": series_id})
            results[series_id] = 0
            continue

        try:
            n = upsert_dataframe(df, table="eia_oil", schema=PG_SCHEMA_RAW, conflict_cols=["date", "series_id"])
            results[series_id] = n
        except Exception:
            logger.exception("Lỗi upsert EIA oil", extra={"series_id": series_id})
            results[series_id] = -1

    logger.info("ingest_eia_with_fallback done", extra={"results": results})
    return results
