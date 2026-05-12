"""
src/data/ingestion/__init__.py
================================
Export tất cả ingestion functions.
Kaggle đã bị xóa — pipeline dùng API thuần (FreeGoldAPI, yfinance, FRED, EIA).
"""

from .freegold_ingestion import fetch_freegoldapi, fetch_gold_yfinance, ingest_gold_prices
from .yfinance_ingestion import fetch_yfinance_ohlcv, ingest_yfinance_all
from .fred_ingestion import fetch_fred_series, ingest_fred_daily, ingest_fred_monthly
from .eia_ingestion import fetch_eia_series, ingest_eia_with_fallback

__all__ = [
    # Gold
    "fetch_freegoldapi",
    "fetch_gold_yfinance",
    "ingest_gold_prices",
    # yfinance
    "fetch_yfinance_ohlcv",
    "ingest_yfinance_all",
    # FRED
    "fetch_fred_series",
    "ingest_fred_daily",
    "ingest_fred_monthly",
    # EIA
    "fetch_eia_series",
    "ingest_eia_with_fallback",
]
