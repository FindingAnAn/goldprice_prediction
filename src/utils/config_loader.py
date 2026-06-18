"""
src/utils/config_loader.py
==========================
Load cấu hình từ .env và config/settings.py.
Import module này để lấy API keys và tất cả paths.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# 1. Load .env từ project root
# ─────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=_ENV_FILE, override=False)

# ─────────────────────────────────────────────
# 2. API Keys
# ─────────────────────────────────────────────
FRED_API_KEY: str = os.getenv("FRED_API_KEY", "")
EIA_API_KEY:  str = os.getenv("EIA_API_KEY",  "")

def _check_key(key: str, name: str) -> bool:
    """Kiểm tra key có hợp lệ không (không rỗng và không phải placeholder)."""
    normalized = key.strip().lower()
    return bool(normalized) and not (
        normalized.startswith("your_")
        or normalized.endswith("_here")
        or "placeholder" in normalized
    )

FRED_KEY_VALID = _check_key(FRED_API_KEY, "FRED_API_KEY")
EIA_KEY_VALID  = _check_key(EIA_API_KEY,  "EIA_API_KEY")

# ─────────────────────────────────────────────
# 3. Re-export tất cả paths từ config/settings.py
# ─────────────────────────────────────────────
from config.settings import (  # noqa: E402
    PROJECT_ROOT,
    DATA_DIR,
    RAW_DIR,
    RAW_INCOMING_DIR,
    PROCESSED_DIR,
    FEATURES_DIR,
    SQL_DIR,
    FREEGOLD_PATH,
    YFINANCE_PATH,
    FRED_PATH,
    EIA_PATH,
    DATA_START_DATE,
    DATA_END_DATE,
    FORECAST_HORIZON_DAYS,
    SUPPORTED_FORECAST_HORIZONS,
    TARGET_COLUMN,
    TARGET_LABEL_COLUMNS,
    POINT_IN_TIME_UNSAFE_FEATURE_COLUMNS,
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
)

__all__ = [
    # Keys
    "FRED_API_KEY", "EIA_API_KEY",
    "FRED_KEY_VALID", "EIA_KEY_VALID",
    # Paths
    "PROJECT_ROOT", "DATA_DIR", "RAW_DIR", "RAW_INCOMING_DIR",
    "PROCESSED_DIR", "FEATURES_DIR", "SQL_DIR",
    "FREEGOLD_PATH", "YFINANCE_PATH", "FRED_PATH", "EIA_PATH",
    # PG Schemas
    "PG_SCHEMA_RAW", "PG_SCHEMA_STAGING", "PG_SCHEMA_FEATURES",
    # Config
    "DATA_START_DATE", "DATA_END_DATE",
    "FORECAST_HORIZON_DAYS", "SUPPORTED_FORECAST_HORIZONS",
    "TARGET_COLUMN", "TARGET_LABEL_COLUMNS",
    "POINT_IN_TIME_UNSAFE_FEATURE_COLUMNS",
    "FREEGOLD_URLS", "YFINANCE_OHLCV_TICKERS",
    "FRED_DAILY_SERIES", "FRED_MONTHLY_SERIES",
    "EIA_BASE_URL", "EIA_SERIES", "EIA_YFINANCE_FALLBACK",
]
