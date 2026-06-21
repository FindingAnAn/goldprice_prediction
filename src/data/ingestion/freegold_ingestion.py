"""
src/data/ingestion/freegold_ingestion.py
=========================================
Fetch gold price history from FreeGoldAPI và upsert vào raw.gold_prices.

FreeGoldAPI cung cấp lịch sử giá vàng daily (từ Yahoo Finance GC=F).
Dữ liệu được filter từ DATA_START_DATE trở đi và upsert vào PostgreSQL.

Functions:
    fetch_freegoldapi      : Download FreeGoldAPI CSV và upsert vào PG.
    fetch_gold_yfinance    : Fetch GC=F từ yfinance làm nguồn bổ sung/cập nhật.
    ingest_gold_prices     : Orchestrate cả hai nguồn, merge và upsert.
"""

from __future__ import annotations

from io import StringIO

import pandas as pd
import requests
import yfinance as yf

from src.utils.config_loader import (
    DATA_END_DATE,
    FREEGOLD_URLS,
    DATA_START_DATE,
    PG_SCHEMA_RAW,
)
from src.utils.logging_config import get_logger
from src.data.storage.postgres_client import upsert_dataframe

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 1. FETCH FREEGOLDAPI
# ─────────────────────────────────────────────────────────────────────────────

def fetch_freegoldapi(
    source: str = "latest",
    start: str = DATA_START_DATE,
    end: str | None = DATA_END_DATE,
) -> pd.DataFrame:
    """Download FreeGoldAPI dataset và trả về DataFrame daily từ `start`.

    Args:
        source : Key trong FREEGOLD_URLS ('latest' hoặc 'gold_silver_ratio').
        start  : Ngày bắt đầu (YYYY-MM-DD), chỉ lấy data từ đây trở đi.

    Returns:
        pd.DataFrame với columns ['date', 'price', 'source'].
        'date' là kiểu DATE (python date object).

    Raises:
        ValueError      : Nếu source không hợp lệ.
        ConnectionError : Nếu HTTP status != 200.
    """
    if source not in FREEGOLD_URLS:
        raise ValueError(
            f"Invalid source '{source}'. Available: {list(FREEGOLD_URLS)}"
        )

    url = FREEGOLD_URLS[source]
    logger.info("Fetching FreeGoldAPI", extra={"source": source, "url": url})

    response = requests.get(url, timeout=30)
    if response.status_code != 200:
        raise ConnectionError(
            f"HTTP {response.status_code} từ FreeGoldAPI. URL: {url}"
        )

    df = pd.read_csv(StringIO(response.text))

    # Chuẩn hóa tên cột
    df.columns = [c.lower().strip() for c in df.columns]

    # Tìm cột giá (price / value / close / gold_price)
    price_col_candidates = ["price", "value", "close", "gold_price", "gold"]
    price_col = next((c for c in price_col_candidates if c in df.columns), None)
    if price_col is None:
        raise ValueError(f"Không tìm thấy cột giá trong FreeGoldAPI. Columns: {list(df.columns)}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df[df["date"] >= start].copy()
    if end is not None:
        df = df[df["date"] <= end].copy()

    # Chỉ giữ daily rows (bỏ monthly trước 2000)
    result = pd.DataFrame({
        "date":   df["date"].dt.date,
        "price":  pd.to_numeric(df[price_col], errors="coerce"),
        "source": "freegoldapi",
    })
    result = result.dropna(subset=["price"]).drop_duplicates(subset=["date"])

    logger.info(
        "FreeGoldAPI fetched",
        extra={"rows": len(result), "start": str(result["date"].min()), "end": str(result["date"].max())},
    )
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 2. FETCH GOLD FROM YFINANCE (GC=F)
# ─────────────────────────────────────────────────────────────────────────────

def fetch_gold_yfinance(
    start: str = DATA_START_DATE,
    end: str | None = DATA_END_DATE,
) -> pd.DataFrame:
    """Fetch Gold Futures (GC=F) daily close từ yfinance.

    yfinance là nguồn cập nhật đến hôm nay (FreeGoldAPI có thể lag vài ngày).
    Kết quả dùng để bổ sung data mới nhất.

    Args:
        start: Ngày bắt đầu YYYY-MM-DD.

    Returns:
        pd.DataFrame với columns ['date', 'price', 'source'].
    """
    logger.info("Fetching GC=F from yfinance", extra={"start": start})

    try:
        from src.data.ingestion.yfinance_ingestion import _exclusive_yfinance_end

        raw = yf.download(
            "GC=F",
            start=start,
            end=_exclusive_yfinance_end(end),
            auto_adjust=True,
            progress=False,
        )
        if raw.empty:
            logger.warning("yfinance GC=F returned an empty DataFrame")
            return pd.DataFrame(columns=["date", "price", "source"])

        close = raw["Close"].squeeze()
        df = pd.DataFrame({
            "date":   close.index.date,
            "price":  close.values,
            "source": "yfinance_gcf",
        })
        df = df.dropna(subset=["price"]).drop_duplicates(subset=["date"])
        logger.info(
            "yfinance GC=F fetched",
            extra={"rows": len(df), "end": str(df["date"].max())},
        )
        return df
    except Exception:
        logger.exception("Failed to fetch GC=F from yfinance")
        return pd.DataFrame(columns=["date", "price", "source"])


# ─────────────────────────────────────────────────────────────────────────────
# 3. ORCHESTRATE + UPSERT
# ─────────────────────────────────────────────────────────────────────────────

def ingest_gold_prices(
    start: str = DATA_START_DATE,
    end: str | None = DATA_END_DATE,
) -> int:
    """Fetch FreeGoldAPI + yfinance GC=F và upsert vào raw.gold_prices.

    Ưu tiên: FreeGoldAPI cho lịch sử, yfinance cho data mới nhất.
    Cả hai nguồn được upsert riêng lẻ — không merge thành 1 row.
    Model downstream sẽ COALESCE theo ưu tiên.

    Args:
        start: Ngày bắt đầu YYYY-MM-DD.

    Returns:
        Tổng số dòng được upsert.
    """
    total = 0

    # FreeGoldAPI
    try:
        df_fg = fetch_freegoldapi(source="latest", start=start, end=end)
        if not df_fg.empty:
            n = upsert_dataframe(
                df_fg,
                table="gold_prices",
                schema=PG_SCHEMA_RAW,
                conflict_cols=["date", "source"],
            )
            total += n
    except Exception:
        logger.exception("FreeGoldAPI ingestion failed")

    # yfinance GC=F
    try:
        df_yf = fetch_gold_yfinance(start=start, end=end)
        if not df_yf.empty:
            n = upsert_dataframe(
                df_yf,
                table="gold_prices",
                schema=PG_SCHEMA_RAW,
                conflict_cols=["date", "source"],
            )
            total += n
    except Exception:
        logger.exception("yfinance GC=F ingestion failed")

    logger.info(
        "Gold price ingestion completed",
        extra={"total_upserted": total},
    )
    return total
