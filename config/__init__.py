"""config/__init__.py — expose settings and tickers at package level."""

from config.settings import (  # noqa: F401
    PROJECT_ROOT,
    DATA_DIR,
    RAW_DIR,
    RAW_INCOMING_DIR,
    PROCESSED_DIR,
    FEATURES_DIR,
    SQL_DIR,
    LOGS_DIR,
    FREEGOLD_PATH,
    YFINANCE_PATH,
    FRED_PATH,
    EIA_PATH,
    DATA_START_DATE,
    DATA_END_DATE,
    PG_SCHEMA_RAW,
    PG_SCHEMA_STAGING,
    PG_SCHEMA_FEATURES,
    FREEGOLD_URLS,
    YFINANCE_OHLCV_TICKERS,
    FRED_DAILY_SERIES,
    FRED_MONTHLY_SERIES,
    EIA_BASE_URL,
    EIA_SERIES,
    EIA_YFINANCE_FALLBACK,
    DatabaseConfig,
)

from config.tickers import (  # noqa: F401
    YFINANCE_TICKERS,
    EIA_FALLBACK_TICKERS,
    GOLD_PRICE_COL,
)
