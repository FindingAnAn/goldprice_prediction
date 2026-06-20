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
-- FRED monthly series (CPI, FEDFUNDS, M2, UNRATE, retail sales, ...)
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

-- ---------------------------------------------------------------------------
-- raw.cftc_gold_positioning
-- Weekly COMEX gold positioning. available_date is the conservative Friday
-- release date used for point-in-time-safe feature joins.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.cftc_gold_positioning (
    report_date                 DATE NOT NULL,
    available_date              DATE NOT NULL,
    contract_code               VARCHAR(12) NOT NULL,
    market_name                 TEXT,
    open_interest               DOUBLE PRECISION,
    producer_long               DOUBLE PRECISION,
    producer_short              DOUBLE PRECISION,
    swap_long                   DOUBLE PRECISION,
    swap_short                  DOUBLE PRECISION,
    managed_money_long          DOUBLE PRECISION,
    managed_money_short         DOUBLE PRECISION,
    managed_money_spread        DOUBLE PRECISION,
    managed_money_long_change   DOUBLE PRECISION,
    managed_money_short_change  DOUBLE PRECISION,
    updated_at                  TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (report_date, contract_code)
);

CREATE INDEX IF NOT EXISTS idx_cftc_gold_available_date
    ON raw.cftc_gold_positioning (available_date);
