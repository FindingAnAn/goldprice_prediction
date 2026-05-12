-- =============================================================================
-- sql/schema/01_raw_tables.sql
-- Tạo schema RAW và các bảng lưu dữ liệu thô từ API.
-- Schemas (raw, staging, features) đã được ensure_schemas() tạo trước.
-- File này chỉ tạo TABLES và INDEXES.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- raw.gold_prices
-- Giá vàng daily từ FreeGoldAPI và yfinance GC=F
-- Source: 'freegoldapi' | 'yfinance_gcf'
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.gold_prices (
    date       DATE             NOT NULL,
    price      DOUBLE PRECISION,
    source     VARCHAR(50)      NOT NULL,
    updated_at TIMESTAMPTZ      DEFAULT NOW(),
    PRIMARY KEY (date, source)
);

CREATE INDEX IF NOT EXISTS idx_gold_prices_date ON raw.gold_prices (date);

-- ---------------------------------------------------------------------------
-- raw.yfinance_daily
-- OHLCV daily data từ Yahoo Finance cho nhiều tickers
-- Tickers: GC=F, DX-Y.NYB, SI=F, ^GSPC, ^VIX, CL=F, BZ=F, ^TNX, ...
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.yfinance_daily (
    date       DATE             NOT NULL,
    ticker     VARCHAR(30)      NOT NULL,
    open       DOUBLE PRECISION,
    high       DOUBLE PRECISION,
    low        DOUBLE PRECISION,
    close      DOUBLE PRECISION,
    volume     DOUBLE PRECISION,
    updated_at TIMESTAMPTZ      DEFAULT NOW(),
    PRIMARY KEY (date, ticker)
);

CREATE INDEX IF NOT EXISTS idx_yfinance_daily_date   ON raw.yfinance_daily (date);
CREATE INDEX IF NOT EXISTS idx_yfinance_daily_ticker ON raw.yfinance_daily (ticker);

-- ---------------------------------------------------------------------------
-- raw.fred_daily
-- FRED daily series (DGS10, DGS2, T10YIE, T10Y2Y, ...)
-- Lưu dạng long: mỗi (date, series_id) là một row
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.fred_daily (
    date       DATE             NOT NULL,
    series_id  VARCHAR(30)      NOT NULL,
    value      DOUBLE PRECISION,
    updated_at TIMESTAMPTZ      DEFAULT NOW(),
    PRIMARY KEY (date, series_id)
);

CREATE INDEX IF NOT EXISTS idx_fred_daily_date      ON raw.fred_daily (date);
CREATE INDEX IF NOT EXISTS idx_fred_daily_series_id ON raw.fred_daily (series_id);

-- ---------------------------------------------------------------------------
-- raw.fred_monthly
-- FRED monthly series (CPI, FEDFUNDS, M2, UNRATE, USINTR, ...)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.fred_monthly (
    date       DATE             NOT NULL,   -- ngày đầu tháng (YYYY-MM-01)
    series_id  VARCHAR(50)      NOT NULL,
    value      DOUBLE PRECISION,
    updated_at TIMESTAMPTZ      DEFAULT NOW(),
    PRIMARY KEY (date, series_id)
);

CREATE INDEX IF NOT EXISTS idx_fred_monthly_date      ON raw.fred_monthly (date);
CREATE INDEX IF NOT EXISTS idx_fred_monthly_series_id ON raw.fred_monthly (series_id);

-- ---------------------------------------------------------------------------
-- raw.eia_oil
-- EIA crude oil spot prices (WTI: RWTC, Brent: RBRTE)
-- Fallback từ yfinance CL=F, BZ=F nếu EIA API lỗi
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.eia_oil (
    date       DATE             NOT NULL,
    series_id  VARCHAR(20)      NOT NULL,
    value      DOUBLE PRECISION,
    updated_at TIMESTAMPTZ      DEFAULT NOW(),
    PRIMARY KEY (date, series_id)
);

CREATE INDEX IF NOT EXISTS idx_eia_oil_date ON raw.eia_oil (date);
