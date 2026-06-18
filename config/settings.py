"""
config/settings.py
==================
Tất cả cấu hình tập trung cho Gold Time Prediction project.
Chỉnh sửa tại đây thay vì rải rác trong notebook.
"""

from pathlib import Path

# ─────────────────────────────────────────────
# 1. PROJECT STRUCTURE
# ─────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR          = PROJECT_ROOT / "data"
RAW_DIR           = DATA_DIR / "raw"
RAW_INCOMING_DIR  = RAW_DIR / "incoming"
PROCESSED_DIR     = DATA_DIR / "processed"
FEATURES_DIR      = DATA_DIR / "features"
SQL_DIR           = PROJECT_ROOT / "sql"
LOGS_DIR          = PROJECT_ROOT / "logs"

# Raw incoming — theo nguồn (giữ lại để backward-compat nếu cần)
FREEGOLD_PATH     = RAW_INCOMING_DIR / "freegoldapi"
YFINANCE_PATH     = RAW_INCOMING_DIR / "yfinance"
FRED_PATH         = RAW_INCOMING_DIR / "fred"
EIA_PATH          = RAW_INCOMING_DIR / "eia"

# ─────────────────────────────────────────────
# 2. TIME RANGE
# ─────────────────────────────────────────────
DATA_START_DATE = "2000-01-01"   # Chỉ dùng daily data từ 2000 trở đi
DATA_END_DATE   = None           # None = đến ngày hôm nay

# Mục tiêu mặc định: giá đóng cửa sau 7 phiên giao dịch.
# SQL target dùng LEAD(..., 7), vì vậy đây là 7 observations/trading sessions,
# không phải 7 ngày lịch và cũng không phải vector gồm 7 giá trị.
FORECAST_HORIZON_DAYS = 7
TARGET_COLUMN = f"next_{FORECAST_HORIZON_DAYS}_day_price"
SUPPORTED_FORECAST_HORIZONS = (1, 3, 7, 30)
TARGET_LABEL_COLUMNS = tuple(
    f"next_{horizon}_day_{target_kind}"
    for horizon in SUPPORTED_FORECAST_HORIZONS
    for target_kind in ("price", "direction", "price_change")
)

# FRED monthly observations are currently stored by observation month, not by
# their historical release timestamp/vintage. Using them in backtests would
# expose values that were not yet available, and possibly later revisions.
POINT_IN_TIME_UNSAFE_FEATURE_COLUMNS = (
    "fed_funds_rate",
    "us_interest_rate",
    "us_inflation_yoy",
    "cpi",
    "core_cpi",
    "m2_money_supply",
    "unemployment_rate",
)

# ─────────────────────────────────────────────
# 3. POSTGRESQL SCHEMAS
# ─────────────────────────────────────────────
PG_SCHEMA_RAW      = "raw"
PG_SCHEMA_STAGING  = "staging"
PG_SCHEMA_FEATURES = "features"

# ─────────────────────────────────────────────
# 4. FREEGOLDAPI (không cần key)
# ─────────────────────────────────────────────
FREEGOLD_URLS = {
    "latest":            "https://freegoldapi.com/data/latest.csv",
    "gold_silver_ratio": "https://freegoldapi.com/data/gold_silver_ratio_enriched.csv",
}

# ─────────────────────────────────────────────
# 5. YFINANCE TICKERS (OHLCV — upsert vào raw.yfinance_daily)
# ─────────────────────────────────────────────
# Gold Futures làm primary gold source (GC=F)
# DXY — Dollar Index (DX-Y.NYB)
# Silver Futures (SI=F)
# S&P 500 (^GSPC)
# Oil futures đã có từ EIA; dùng yfinance làm fallback
YFINANCE_OHLCV_TICKERS = [
    "GC=F",       # Gold Futures  → gold OHLCV + volume
    "DX-Y.NYB",   # US Dollar Index (DXY) OHLCV
    "SI=F",       # Silver Futures
    "^GSPC",      # S&P 500
    "^VIX",       # CBOE VIX (chỉ có Close)
    "CL=F",       # WTI Oil (fallback EIA)
    "BZ=F",       # Brent Oil (fallback EIA)
    "^TNX",       # 10Y Treasury Yield
    "^IRX",       # 13-week T-bill rate
    "GLD",        # SPDR Gold Shares ETF (volume proxy)
    "SLV",        # iShares Silver Trust
    "TLT",        # 20+ Year Treasury Bond ETF
    "UUP",        # Invesco US Dollar Bullish ETF
    "^TYX",       # 30-Year Treasury Yield (fallback when FRED lags/unavailable)
]

# ─────────────────────────────────────────────
# 6. FRED SERIES IDs
# ─────────────────────────────────────────────
FRED_DAILY_SERIES = {
    "DGS10":    "US_10Y_Yield",          # 10-Year Treasury Yield (Daily)
    "DGS2":     "US_2Y_Yield",           # 2-Year Treasury Yield (Daily)
    "DGS30":    "US_30Y_Yield",          # 30-Year Treasury Yield (Daily)
    "T10YIE":   "Breakeven_Inflation",   # 10-Year Breakeven Inflation (Daily)
    "DTWEXBGS": "DXY_Dollar_Index",      # US Dollar Broad Index (Daily)
    "SP500":    "SP500",                 # S&P 500 Index (Daily)
    "VIXCLS":   "VIX",                   # CBOE VIX Index (Daily)
    "T10Y2Y":   "Yield_Curve_Slope",     # 10Y minus 2Y spread (Daily)
}

FRED_MONTHLY_SERIES = {
    "CPIAUCSL": "CPI",                   # Consumer Price Index (Monthly)
    "CPILFESL": "Core_CPI",             # Core CPI ex food/energy (Monthly)
    "FEDFUNDS": "Fed_Funds_Rate",        # Federal Funds Rate (Monthly)
    "RSXFS":    "Retail_Sales",          # Retail Sales (Monthly)
    "UNRATE":   "Unemployment_Rate",     # Unemployment Rate (Monthly)
    "M2SL":     "M2_Money_Supply",       # M2 Money Supply (Monthly)
}

# ─────────────────────────────────────────────
# 7. EIA SERIES IDs  (fallback → yfinance nếu lỗi)
# ─────────────────────────────────────────────
EIA_BASE_URL = "https://api.eia.gov/v2/petroleum/pri/spt/data/"

EIA_SERIES = {
    "RWTC":  "WTI_Oil_Price",    # WTI Crude Oil Spot Price (Daily)
    "RBRTE": "Brent_Oil_Price",  # Brent Crude Oil Spot Price (Daily)
}

# Yfinance symbols dùng làm fallback khi EIA lỗi
EIA_YFINANCE_FALLBACK = {
    "RWTC":  "CL=F",   # WTI futures
    "RBRTE": "BZ=F",   # Brent futures
}


# ─────────────────────────────────────────────
# 8. DATABASE CONFIG
# ─────────────────────────────────────────────
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseConfig:
    """Typed database configuration loaded from environment variables.

    All database-related ``os.getenv()`` calls are centralised here
    so that no other module needs to read raw environment variables.

    Args:
        host: PostgreSQL host address.
        port: PostgreSQL port number.
        user: Database user name.
        password: Database password.
        dbname: Database name.
    """

    host: str = "127.0.0.1"
    port: int = 5432
    user: str = "postgres"
    password: str = ""
    dbname: str = "postgres"

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create a DatabaseConfig by reading DB_* environment variables.

        Returns:
            DatabaseConfig populated from the environment.
        """
        return cls(
            host=os.getenv("DB_HOST", os.getenv("PG_HOST", "127.0.0.1")),
            port=int(os.getenv("DB_PORT", os.getenv("PG_PORT", "5432"))),
            user=os.getenv(
                "DB_USER",
                os.getenv("PG_USER", os.getenv("PG_USERNAME", "postgres")),
            ),
            password=os.getenv("DB_PASSWORD", os.getenv("PG_PASSWORD", "")),
            dbname=os.getenv("DB_NAME", os.getenv("PG_DB", "postgres")),
        )

    @property
    def sqlalchemy_url(self) -> str:
        """Return a ``postgresql+psycopg2://`` connection URL."""
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"

    def to_psycopg2_params(self) -> dict:
        """Return a dict suitable for ``psycopg2.connect(**params)``."""
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "dbname": self.dbname,
        }
