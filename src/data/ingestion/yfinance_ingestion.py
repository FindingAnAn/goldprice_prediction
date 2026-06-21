"""
src/data/ingestion/yfinance_ingestion.py
=========================================
Download OHLCV từ Yahoo Finance cho nhiều tickers và upsert vào raw.yfinance_daily.

Tickers được định nghĩa trong config/settings.py (YFINANCE_OHLCV_TICKERS).
Bao gồm DXY (DX-Y.NYB), Gold Futures (GC=F), Silver (SI=F), Oil (CL=F, BZ=F), v.v.

Functions:
    fetch_yfinance_ohlcv : Download OHLCV một ticker từ yfinance.
    ingest_yfinance_all  : Fetch tất cả tickers và upsert vào PG.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

from src.utils.config_loader import (
    DATA_END_DATE,
    DATA_START_DATE,
    YFINANCE_OHLCV_TICKERS,
    PG_SCHEMA_RAW,
)
from src.utils.logging_config import get_logger
from src.data.storage.postgres_client import upsert_dataframe

logger = get_logger(__name__)


NEW_YORK_TZ = ZoneInfo("America/New_York")
SAFE_MARKET_CLOSE = time(18, 0)


def _latest_complete_market_date(now: datetime | None = None) -> date:
    """Return the latest date whose US market session is safely complete."""

    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    new_york_now = reference.astimezone(NEW_YORK_TZ)

    if (
        new_york_now.weekday() < 5
        and new_york_now.time() >= SAFE_MARKET_CLOSE
    ):
        candidate = new_york_now.date()
    else:
        candidate = new_york_now.date() - timedelta(days=1)

    while candidate.weekday() >= 5:
        candidate -= timedelta(days=1)
    return candidate


def _exclusive_yfinance_end(
    end: str | None,
    now: datetime | None = None,
) -> str:
    """Convert an inclusive complete-session date to Yahoo's exclusive end."""

    inclusive_end = (
        date.fromisoformat(end)
        if end is not None
        else _latest_complete_market_date(now=now)
    )
    return (inclusive_end + timedelta(days=1)).isoformat()


# ─────────────────────────────────────────────────────────────────────────────
# 1. FETCH OHLCV CHO MỘT TICKER
# ─────────────────────────────────────────────────────────────────────────────

def fetch_yfinance_ohlcv(
    ticker: str,
    start: str = DATA_START_DATE,
    end: str | None = DATA_END_DATE,
) -> pd.DataFrame:
    """Download OHLCV daily data cho một ticker từ Yahoo Finance.

    Args:
        ticker : Yahoo Finance symbol (e.g. 'GC=F', 'DX-Y.NYB', '^GSPC').
        start  : Start date YYYY-MM-DD.
        end    : End date YYYY-MM-DD. Nếu None = phiên Mỹ đã hoàn tất gần nhất.

    Returns:
        pd.DataFrame với columns ['date', 'ticker', 'open', 'high', 'low', 'close', 'volume'].
        'date' là kiểu DATE.
        Trả về DataFrame rỗng nếu lỗi hoặc không có data.
    """
    logger.info("Fetching yfinance OHLCV", extra={"ticker": ticker, "start": start})

    try:
        raw = yf.download(
            ticker,
            start=start,
            end=_exclusive_yfinance_end(end),
            auto_adjust=True,
            progress=False,
        )
    except Exception:
        logger.exception("yfinance download failed", extra={"ticker": ticker})
        return pd.DataFrame()

    if raw.empty:
        logger.warning("yfinance returned no rows", extra={"ticker": ticker})
        return pd.DataFrame()

    # Flatten MultiIndex columns nếu có (xảy ra với single ticker đôi khi)
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    raw.columns = [c.lower() for c in raw.columns]

    # Chọn các cột cần thiết
    ohlcv_cols = ["open", "high", "low", "close", "volume"]
    existing = [c for c in ohlcv_cols if c in raw.columns]
    raw = raw[existing].copy()

    # Thêm cột ticker và chuẩn hóa date
    raw.index.name = "date"
    raw = raw.reset_index()
    raw["date"]   = pd.to_datetime(raw["date"]).dt.date
    raw["ticker"] = ticker

    # Đảm bảo đủ cột, fill None nếu thiếu
    for col in ohlcv_cols:
        if col not in raw.columns:
            raw[col] = None

    result = raw[["date", "ticker"] + ohlcv_cols].copy()
    result = result.dropna(subset=["close"]).drop_duplicates(subset=["date", "ticker"])

    logger.info(
        "yfinance OHLCV fetched",
        extra={"ticker": ticker, "rows": len(result), "end": str(result["date"].max()) if len(result) else "N/A"},
    )
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 2. INGEST TẤT CẢ TICKERS → PG
# ─────────────────────────────────────────────────────────────────────────────

def ingest_yfinance_all(
    tickers: list[str] = YFINANCE_OHLCV_TICKERS,
    start: str = DATA_START_DATE,
    end: str | None = DATA_END_DATE,
) -> dict[str, int]:
    """Fetch OHLCV cho tất cả tickers và upsert vào raw.yfinance_daily.

    Args:
        tickers : Danh sách Yahoo Finance symbols.
        start   : Start date YYYY-MM-DD.

    Returns:
        Dict mapping ticker → số dòng được upsert.
    """
    results: dict[str, int] = {}

    for ticker in tickers:
        try:
            df = fetch_yfinance_ohlcv(ticker=ticker, start=start, end=end)
            if df.empty:
                results[ticker] = 0
                continue

            n = upsert_dataframe(
                df,
                table="yfinance_daily",
                schema=PG_SCHEMA_RAW,
                conflict_cols=["date", "ticker"],
            )
            results[ticker] = n

        except Exception:
            logger.exception(
                "yfinance ticker ingestion failed",
                extra={"ticker": ticker},
            )
            results[ticker] = -1

    success = sum(v for v in results.values() if v > 0)
    logger.info(
        "yfinance ingestion completed",
        extra={"total_upserted": success, "tickers_count": len(tickers)},
    )
    return results
