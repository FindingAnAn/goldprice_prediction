"""
config/tickers.py
=================
Định nghĩa tất cả yfinance tickers dùng trong dự án.
Key = Yahoo Finance symbol, Value = tên cột trong DataFrame.
"""

# ─────────────────────────────────────────────
# YFINANCE TICKERS — Daily Close Price
# ─────────────────────────────────────────────
YFINANCE_TICKERS = {
    # Precious Metals
    "GC=F":     "Gold_Close",          # Gold Futures (COMEX)
    "SI=F":     "Silver_Close",        # Silver Futures (COMEX)

    # Energy (backup nếu EIA API lỗi sẽ dùng thêm CL=F, BZ=F)
    "CL=F":     "WTI_Oil_Close",       # WTI Crude Oil Futures
    "BZ=F":     "Brent_Oil_Close",     # Brent Crude Oil Futures

    # Equity Market
    "^GSPC":    "SP500_Close",         # S&P 500 Index
    "GLD":      "Gold_ETF_Close",      # SPDR Gold Shares ETF

    # Volatility
    "^VIX":     "VIX_Close",           # CBOE Volatility Index

    # Currencies & Rates
    "DX-Y.NYB": "DXY_Close",           # US Dollar Index (ICE)
    "^TNX":     "US_10Y_Yield_YF",     # US 10Y Treasury Yield (Yahoo)
    "^TYX":     "US_30Y_Yield_YF",     # US 30Y Treasury Yield (Yahoo)
}

# ─────────────────────────────────────────────
# EIA FALLBACK TICKERS — chỉ dùng nếu EIA API lỗi
# ─────────────────────────────────────────────
EIA_FALLBACK_TICKERS = {
    "CL=F": "WTI_Oil_Close",
    "BZ=F": "Brent_Oil_Close",
}

# ─────────────────────────────────────────────
# GOLD COLUMN — tên cột giá vàng chính trong df_daily
# ─────────────────────────────────────────────
GOLD_PRICE_COL = "Gold_Close"   # từ yfinance GC=F
