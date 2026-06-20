-- =============================================================================
-- sql/schema/02_staging_tables.sql
-- Tạo bảng staging.daily_master — merge tất cả nguồn dữ liệu.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- staging.daily_master
-- One row per trading day. Merge từ raw tables.
-- Gold price ưu tiên yfinance_gcf (mới hơn) rồi đến freegoldapi.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.daily_master (
    date                DATE             NOT NULL PRIMARY KEY,

    -- ── Gold Price (label) ─────────────────────────────────────────────────
    gold_close          DOUBLE PRECISION,   -- COALESCE(yfinance GC=F, freegoldapi)
    gold_open           DOUBLE PRECISION,
    gold_high           DOUBLE PRECISION,
    gold_low            DOUBLE PRECISION,
    gold_volume         DOUBLE PRECISION,

    -- ── DXY (US Dollar Index) ──────────────────────────────────────────────
    dxy_open            DOUBLE PRECISION,
    dxy_high            DOUBLE PRECISION,
    dxy_low             DOUBLE PRECISION,
    dxy_close           DOUBLE PRECISION,

    -- ── Silver ────────────────────────────────────────────────────────────
    silver_close        DOUBLE PRECISION,

    -- ── Oil ───────────────────────────────────────────────────────────────
    wti_oil_price       DOUBLE PRECISION,
    brent_oil_price     DOUBLE PRECISION,

    -- ── Equity & Volatility ───────────────────────────────────────────────
    sp500_close         DOUBLE PRECISION,
    vix                 DOUBLE PRECISION,

    -- ── FRED Daily ────────────────────────────────────────────────────────
    us_10y_yield        DOUBLE PRECISION,   -- DGS10
    us_2y_yield         DOUBLE PRECISION,   -- DGS2
    us_30y_yield        DOUBLE PRECISION,   -- DGS30
    breakeven_inflation DOUBLE PRECISION,   -- T10YIE
    yield_curve_slope   DOUBLE PRECISION,   -- T10Y2Y (10Y - 2Y)

    -- ── FRED Monthly (forward-filled vào daily) ───────────────────────────
    fed_funds_rate      DOUBLE PRECISION,   -- FEDFUNDS
    cpi                 DOUBLE PRECISION,   -- CPIAUCSL
    core_cpi            DOUBLE PRECISION,   -- CPILFESL
    unemployment_rate   DOUBLE PRECISION,   -- UNRATE
    m2_money_supply     DOUBLE PRECISION,   -- M2SL

    -- ── Metadata ──────────────────────────────────────────────────────────
    is_outlier          BOOLEAN          DEFAULT FALSE,
    updated_at          TIMESTAMPTZ      DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_staging_daily_date ON staging.daily_master (date);

ALTER TABLE staging.daily_master
    DROP COLUMN IF EXISTS silver_open,
    DROP COLUMN IF EXISTS silver_high,
    DROP COLUMN IF EXISTS silver_low,
    DROP COLUMN IF EXISTS us_interest_rate,
    DROP COLUMN IF EXISTS us_inflation_yoy,
    DROP COLUMN IF EXISTS retail_sales;

DROP TABLE IF EXISTS staging.monthly_master;
