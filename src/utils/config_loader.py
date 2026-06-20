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
    LOGS_DIR,
    PREDICTIONS_DIR,
    FREEGOLD_PATH,
    YFINANCE_PATH,
    FRED_PATH,
    EIA_PATH,
    CFTC_PATH,
    DATA_START_DATE,
    DATA_END_DATE,
    OPEN_FORECAST_HORIZON,
    OPEN_TARGET_COLUMNS,
    OPEN_FORECAST_RANDOM_SEED,
    OPEN_FORECAST_TEST_SIZE,
    OPEN_FORECAST_CV_SPLITS,
    OPEN_FORECAST_MODEL_CONFIG,
    OPEN_FORECAST_FLAT_THRESHOLD_PCT,
    POINT_IN_TIME_UNSAFE_FEATURE_COLUMNS,
    PG_SCHEMA_RAW,
    PG_SCHEMA_STAGING,
    PG_SCHEMA_FEATURES,
    PG_SCHEMA_FORECASTING,
    FREEGOLD_URLS,
    YFINANCE_OHLCV_TICKERS,
    FRED_DAILY_SERIES,
    FRED_MONTHLY_SERIES,
    EIA_BASE_URL,
    EIA_SERIES,
    EIA_YFINANCE_FALLBACK,
    CFTC_HISTORY_URL_TEMPLATE,
    CFTC_CURRENT_URL,
    CFTC_GOLD_CONTRACT_CODE,
    CFTC_FIRST_DISAGGREGATED_YEAR,
    DEEP_FORECAST_MODELS,
    DEEP_FORECAST_HORIZONS,
    DEEP_FORECAST_INPUT_SIZE,
    DEEP_FORECAST_VALIDATION_SIZE,
    DEEP_FORECAST_DEFAULT_WINDOWS,
    DEEP_FORECAST_DEFAULT_MAX_STEPS,
    DEEP_FORECAST_MIN_EXOG_COVERAGE,
    DEEP_FORECAST_HIST_EXOG,
)

__all__ = [
    # Keys
    "FRED_API_KEY", "EIA_API_KEY",
    "FRED_KEY_VALID", "EIA_KEY_VALID",
    # Paths
    "PROJECT_ROOT", "DATA_DIR", "RAW_DIR", "RAW_INCOMING_DIR",
    "PROCESSED_DIR", "FEATURES_DIR", "SQL_DIR", "LOGS_DIR",
    "PREDICTIONS_DIR",
    "FREEGOLD_PATH", "YFINANCE_PATH", "FRED_PATH", "EIA_PATH", "CFTC_PATH",
    # PG Schemas
    "PG_SCHEMA_RAW", "PG_SCHEMA_STAGING", "PG_SCHEMA_FEATURES",
    "PG_SCHEMA_FORECASTING",
    # Config
    "DATA_START_DATE", "DATA_END_DATE",
    "OPEN_FORECAST_HORIZON", "OPEN_TARGET_COLUMNS",
    "OPEN_FORECAST_RANDOM_SEED", "OPEN_FORECAST_TEST_SIZE",
    "OPEN_FORECAST_CV_SPLITS", "OPEN_FORECAST_MODEL_CONFIG",
    "OPEN_FORECAST_FLAT_THRESHOLD_PCT",
    "POINT_IN_TIME_UNSAFE_FEATURE_COLUMNS",
    "FREEGOLD_URLS", "YFINANCE_OHLCV_TICKERS",
    "FRED_DAILY_SERIES", "FRED_MONTHLY_SERIES",
    "EIA_BASE_URL", "EIA_SERIES", "EIA_YFINANCE_FALLBACK",
    "CFTC_HISTORY_URL_TEMPLATE", "CFTC_CURRENT_URL",
    "CFTC_GOLD_CONTRACT_CODE",
    "CFTC_FIRST_DISAGGREGATED_YEAR",
    "DEEP_FORECAST_MODELS", "DEEP_FORECAST_HORIZONS",
    "DEEP_FORECAST_INPUT_SIZE", "DEEP_FORECAST_VALIDATION_SIZE",
    "DEEP_FORECAST_DEFAULT_WINDOWS", "DEEP_FORECAST_DEFAULT_MAX_STEPS",
    "DEEP_FORECAST_MIN_EXOG_COVERAGE", "DEEP_FORECAST_HIST_EXOG",
]
