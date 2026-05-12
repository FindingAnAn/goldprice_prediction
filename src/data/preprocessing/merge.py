"""
src/data/preprocessing/merge.py
==================================
Time format standardization. merge.py giờ chỉ được dùng làm
utility (normalize_datetime) — pipeline chính dùng SQL/PostgreSQL.

Không còn tham chiếu Kaggle. Base data là FreeGoldAPI + yfinance GC=F.
"""

from __future__ import annotations

import pandas as pd

from src.utils.config_loader import DATA_START_DATE


_DATE_COL_CANDIDATES = ["time", "date", "period", "Date", "TIME", "DATE"]


def normalize_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize DataFrame về DatetimeIndex chuẩn (tz-naive, index.name='date', sorted asc).

    Logic:
        1. Nếu index đã là DatetimeIndex: strip tz, rename 'date', sort.
        2. Nếu không: tìm cột date-like, parse, set làm index.

    Args:
        df: Raw DataFrame từ bất kỳ nguồn nào.

    Returns:
        pd.DataFrame với DatetimeIndex (tz-naive, name='date', sorted asc).

    Raises:
        ValueError: Nếu không tìm thấy cột date-like.
    """
    if df is None or df.empty:
        return df

    if isinstance(df.index, pd.DatetimeIndex):
        df = df.copy()
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        df.index.name = "date"
        return df.sort_index()

    df = df.copy()
    date_col = next((c for c in _DATE_COL_CANDIDATES if c in df.columns), None)

    if date_col is None:
        raise ValueError(f"No date column found. Columns: {list(df.columns)}")

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col]).set_index(date_col)
    df.index.name = "date"
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    return df.sort_index()


def build_daily_master(
    df_gold: pd.DataFrame,
    df_yf: pd.DataFrame,
    df_fred_d: pd.DataFrame,
    df_oil: pd.DataFrame,
    start: str = DATA_START_DATE,
) -> pd.DataFrame:
    """Merge daily sources thành một DataFrame (dùng cho kiểm tra/EDA nhanh).

    Trong production pipeline chính, việc merge được thực hiện bằng SQL
    trong staging.daily_master. Hàm này chỉ dùng cho debug/notebook.

    Source priority:
        1. FreeGoldAPI / yfinance GC=F  — base (gold price)
        2. yfinance OHLCV               — add new columns only
        3. FRED daily                   — add new columns only
        4. EIA / fallback               — add new columns only

    Args:
        df_gold  : Gold price DataFrame (từ FreeGoldAPI hoặc yfinance GC=F).
        df_yf    : yfinance OHLCV DataFrame (wide format).
        df_fred_d: FRED daily DataFrame (wide format).
        df_oil   : EIA/yfinance oil prices.
        start    : Filter từ ngày này trở đi.

    Returns:
        pd.DataFrame với DatetimeIndex ('date'), forward-filled tối đa 3 ngày.
    """
    base = normalize_datetime(df_gold)

    extras = []
    for df_extra in [df_yf, df_fred_d, df_oil]:
        if df_extra is not None and not df_extra.empty:
            norm = normalize_datetime(df_extra)
            new_cols = [c for c in norm.columns if c not in base.columns]
            if new_cols:
                extras.append(norm[new_cols])

    merged = pd.concat([base] + extras, axis=1)
    merged.index.name = "date"
    merged = merged[merged.index >= start].sort_index()
    merged = merged.ffill(limit=3)
    return merged
