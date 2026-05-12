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
    "USINTR":   "US_Interest_Rate",      # US Interest Rate (Monthly) → usintr
    "FPCPITOTLZGUSA": "US_Inflation_YoY", # US Inflation YoY → usiryy
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
