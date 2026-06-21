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
PREDICTIONS_DIR   = DATA_DIR / "predictions"

# Raw incoming — theo nguồn (giữ lại để backward-compat nếu cần)
FREEGOLD_PATH     = RAW_INCOMING_DIR / "freegoldapi"
YFINANCE_PATH     = RAW_INCOMING_DIR / "yfinance"
FRED_PATH         = RAW_INCOMING_DIR / "fred"
EIA_PATH          = RAW_INCOMING_DIR / "eia"
CFTC_PATH         = RAW_INCOMING_DIR / "cftc"

# ─────────────────────────────────────────────
# 2. TIME RANGE
# ─────────────────────────────────────────────
DATA_START_DATE = "2010-01-01"   # Đồng bộ lịch sử với CFTC disaggregated COT
DATA_END_DATE   = None           # None = đến ngày hôm nay

OPEN_FORECAST_HORIZON = 10
OPEN_FORECAST_RANDOM_SEED = 42
OPEN_FORECAST_MODEL_CONFIG = {
    "benchmark_family": "hybrid_sequence_and_direct_tabular",
    "mandatory_models": (
        "TiDE",
        "PatchTST",
        "NHITS",
        "DLinear",
        "NLinear",
        "RidgeDirect",
        "XGBoostDirect",
        "LightGBMDirect",
        "RidgeXGBoostBlend",
    ),
}
OPEN_FORECAST_FLAT_THRESHOLD_PCT = 0.05
OPEN_TARGET_COLUMNS = tuple(
    f"next_{horizon}_day_open"
    for horizon in range(1, OPEN_FORECAST_HORIZON + 1)
)

# FRED monthly observations are currently stored by observation month, not by
# their historical release timestamp/vintage. Using them in backtests would
# expose values that were not yet available, and possibly later revisions.
POINT_IN_TIME_UNSAFE_FEATURE_COLUMNS = (
    "fed_funds_rate",
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
PG_SCHEMA_FORECASTING = "forecasting"

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
    "TIP",        # US Treasury Inflation-Protected Securities ETF
    "HYG",        # US High-Yield Corporate Bond ETF
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
    "DFII10":   "US_10Y_Real_Yield",     # 10Y TIPS real yield (Daily)
    "USEPUINDXD": "US_Economic_Policy_Uncertainty",  # News-based EPU (Daily)
    "BAMLH0A0HYM2": "US_High_Yield_OAS", # Credit-risk spread (Daily)
}

FRED_MONTHLY_SERIES = {
    "CPIAUCSL": "CPI",                   # Consumer Price Index (Monthly)
    "CPILFESL": "Core_CPI",             # Core CPI ex food/energy (Monthly)
    "FEDFUNDS": "Fed_Funds_Rate",        # Federal Funds Rate (Monthly)
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

# CFTC Disaggregated Futures-Only annual archives. The report describes
# Tuesday positions and is normally released Friday; available_date therefore
# uses a conservative +3 calendar-day lag for point-in-time-safe joins.
CFTC_HISTORY_URL_TEMPLATE = (
    "https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip"
)
CFTC_CURRENT_URL = "https://www.cftc.gov/dea/newcot/f_disagg.txt"
CFTC_GOLD_CONTRACT_CODE = "088691"
CFTC_FIRST_DISAGGREGATED_YEAR = 2010

# Sequence benchmark: nonlinear deep models plus intentionally simple linear
# challengers. DLinear/NLinear are important controls because simple linear
# architectures can outperform transformers on small or shifting datasets.
DEEP_FORECAST_MODELS = (
    "TiDE",
    "PatchTST",
    "NHITS",
    "DLinear",
    "NLinear",
)
DEEP_FORECAST_HORIZONS = (1, 3, 5, 7, 10)
DEEP_FORECAST_INPUT_SIZE = 252
DEEP_FORECAST_VALIDATION_SIZE = 63
DEEP_FORECAST_DEFAULT_WINDOWS = 6
DEEP_FORECAST_DEFAULT_MAX_STEPS = 100
DEEP_FORECAST_MIN_EXOG_COVERAGE = 0.80
DEEP_FORECAST_HIST_EXOG = (
    "gold_close",
    "dxy_close",
    "real_yield",
    "real_yield_change_5d",
    "vix",
    "vix_change_5d",
    "gold_silver_ratio",
    "gold_pct_chg_21d",
    "ewma_vol_30d",
    "economic_policy_uncertainty",
    "epu_zscore_63d",
    "cftc_mm_net_pct_oi",
    "cftc_mm_net_change_pct_oi",
    "gld_volume_zscore_21d",
)

# Direct multi-horizon tabular models predict the log return from the current
# close to each future open. This target is more stationary than the raw price
# level and each horizon is trained independently to avoid recursive error.
TABULAR_FORECAST_MODELS = (
    "RidgeDirect",
    "XGBoostDirect",
    "LightGBMDirect",
)
TABULAR_FORECAST_ENSEMBLES = {
    "RidgeXGBoostBlend": ("RidgeDirect", "XGBoostDirect"),
}
TABULAR_FORECAST_TRAINING_WINDOW = 1260  # approximately five trading years
TABULAR_FORECAST_WINDOWS = (5, 10, 21, 63, 126, 252)
TABULAR_FORECAST_LAGS = (1, 2, 3, 5, 10, 21, 63, 126, 252)
TABULAR_FORECAST_BASE_FEATURES = (
    "gold_open",
    "gold_high",
    "gold_low",
    "gold_close",
    "gold_volume",
    "dxy_close",
    "silver_close",
    "wti_oil_price",
    "brent_oil_price",
    "sp500_close",
    "vix",
    "us_10y_yield",
    "us_2y_yield",
    "us_30y_yield",
    "breakeven_inflation",
    "yield_curve_slope",
    "real_yield",
    "us_10y_real_yield",
    "gold_silver_ratio",
    "gold_oil_ratio",
    "gold_sp500_ratio",
    "gold_dxy_ratio",
    "oil_spread",
    "dxy_return_5d",
    "real_yield_change_5d",
    "vix_change_5d",
    "sp500_return_5d",
    "gld_return_5d",
    "gld_volume_zscore_21d",
    "tlt_return_5d",
    "uup_return_5d",
    "tip_return_5d",
    "hyg_return_5d",
    "economic_policy_uncertainty",
    "epu_zscore_63d",
    "high_yield_spread",
    "high_yield_spread_change_5d",
    "cftc_mm_net_pct_oi",
    "cftc_mm_net_change_pct_oi",
    "cftc_producer_net_pct_oi",
    "cftc_swap_net_pct_oi",
    "cftc_mm_net_zscore_52w",
    "cftc_positioning_age_days",
    "month_sin",
    "month_cos",
    "year_sin",
    "year_cos",
    "month_progress",
    "quarter_progress",
    "year_progress",
    "days_to_year_end",
    "month_to_date_return",
    "quarter_to_date_return",
    "year_to_date_return",
    "same_month_return_5d_mean",
    "same_month_up_rate_5d",
    "same_month_return_21d_mean",
    "same_month_up_rate_21d",
    "same_quarter_return_21d_mean",
    "same_quarter_up_rate_21d",
    "same_doy_return_5d_mean",
    "same_doy_up_rate_5d",
    "same_doy_return_10d_mean",
    "same_doy_up_rate_10d",
    "regime_return_5d_mean",
    "regime_up_rate_5d",
    "regime_return_10d_mean",
    "regime_up_rate_10d",
)


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
