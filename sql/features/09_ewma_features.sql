-- =============================================================================
-- sql/features/09_ewma_features.sql
-- Tính EWMA (Exponential Weighted Moving Average) cho gold_close.
-- Window sizes: 7d, 30d, 90d, 365d (calendar days ≈ 5, 21, 63, 252 trading days).
--
-- PostgreSQL không có hàm EWMA built-in.
-- Dùng Exponential Weighted Window (EWWMA):
--   EWMA_t = SUM(close_i * w_i) / SUM(w_i)
--   w_i = alpha * (1 - alpha)^(t - i)   với alpha = 2 / (span + 1)
--
-- Span mapping (calendar → trading days → alpha):
--   7d  → span =   5  → alpha = 2/6   ≈ 0.3333
--   30d → span =  21  → alpha = 2/22  ≈ 0.0909
--   90d → span =  63  → alpha = 2/64  ≈ 0.0308
--  365d → span = 252  → alpha = 2/253 ≈ 0.0079
--
-- Lưu vào features.ewma_features.
-- Tất cả ROWS BETWEEN N PRECEDING AND CURRENT ROW — KHÔNG có future data.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Helper: tính row-number để xác định khoảng cách relative giữa các rows
-- ---------------------------------------------------------------------------
WITH base AS (
    SELECT
        date,
        gold_close,
        gold_volume,
        ROW_NUMBER() OVER (ORDER BY date) AS rn
    FROM staging.daily_master
    WHERE gold_close IS NOT NULL
      AND date >= '2000-01-01'
),

-- ---------------------------------------------------------------------------
-- EWMA 7-day calendar ≈ span 5 trading days (alpha = 2/6)
-- Window: 4 PRECEDING (total 5 rows = span)
-- ---------------------------------------------------------------------------
ewma_7d AS (
    SELECT
        date,
        SUM(gold_close * POWER(1.0 - 2.0/6.0, rn - sub_rn)) OVER w5
            / NULLIF(SUM(POWER(1.0 - 2.0/6.0, rn - sub_rn)) OVER w5, 0)
            AS ewma_7d,

        -- EWMA của volume cùng window
        SUM(gold_volume * POWER(1.0 - 2.0/6.0, rn - sub_rn)) OVER w5
            / NULLIF(SUM(POWER(1.0 - 2.0/6.0, rn - sub_rn)) OVER w5, 0)
            AS ewma_vol_7d
    FROM (SELECT *, rn AS sub_rn FROM base) sub
    WINDOW w5 AS (ORDER BY date ROWS BETWEEN 4 PRECEDING AND CURRENT ROW)
),

-- ---------------------------------------------------------------------------
-- EWMA 30-day calendar ≈ span 21 trading days (alpha = 2/22)
-- Window: 20 PRECEDING (total 21 rows = span)
-- ---------------------------------------------------------------------------
ewma_30d AS (
    SELECT
        date,
        SUM(gold_close * POWER(1.0 - 2.0/22.0, rn - sub_rn)) OVER w21
            / NULLIF(SUM(POWER(1.0 - 2.0/22.0, rn - sub_rn)) OVER w21, 0)
            AS ewma_30d,

        SUM(gold_volume * POWER(1.0 - 2.0/22.0, rn - sub_rn)) OVER w21
            / NULLIF(SUM(POWER(1.0 - 2.0/22.0, rn - sub_rn)) OVER w21, 0)
            AS ewma_vol_30d
    FROM (SELECT *, rn AS sub_rn FROM base) sub
    WINDOW w21 AS (ORDER BY date ROWS BETWEEN 20 PRECEDING AND CURRENT ROW)
),

-- ---------------------------------------------------------------------------
-- EWMA 90-day calendar ≈ span 63 trading days (alpha = 2/64)
-- Window: 62 PRECEDING (total 63 rows = span)
-- ---------------------------------------------------------------------------
ewma_90d AS (
    SELECT
        date,
        SUM(gold_close * POWER(1.0 - 2.0/64.0, rn - sub_rn)) OVER w63
            / NULLIF(SUM(POWER(1.0 - 2.0/64.0, rn - sub_rn)) OVER w63, 0)
            AS ewma_90d,

        SUM(gold_volume * POWER(1.0 - 2.0/64.0, rn - sub_rn)) OVER w63
            / NULLIF(SUM(POWER(1.0 - 2.0/64.0, rn - sub_rn)) OVER w63, 0)
            AS ewma_vol_90d
    FROM (SELECT *, rn AS sub_rn FROM base) sub
    WINDOW w63 AS (ORDER BY date ROWS BETWEEN 62 PRECEDING AND CURRENT ROW)
),

-- ---------------------------------------------------------------------------
-- EWMA 365-day calendar ≈ span 252 trading days (alpha = 2/253)
-- Window: 251 PRECEDING (total 252 rows = span)
-- ---------------------------------------------------------------------------
ewma_365d AS (
    SELECT
        date,
        SUM(gold_close * POWER(1.0 - 2.0/253.0, rn - sub_rn)) OVER w252
            / NULLIF(SUM(POWER(1.0 - 2.0/253.0, rn - sub_rn)) OVER w252, 0)
            AS ewma_365d,

        SUM(gold_volume * POWER(1.0 - 2.0/253.0, rn - sub_rn)) OVER w252
            / NULLIF(SUM(POWER(1.0 - 2.0/253.0, rn - sub_rn)) OVER w252, 0)
            AS ewma_vol_365d
    FROM (SELECT *, rn AS sub_rn FROM base) sub
    WINDOW w252 AS (ORDER BY date ROWS BETWEEN 251 PRECEDING AND CURRENT ROW)
),

-- ---------------------------------------------------------------------------
-- EWMA Signal: % khoảng cách giữa price và EWMA (momentum indicator)
--   > 0 → giá đang TRÊN EWMA (bullish)
--   < 0 → giá đang DƯỚI EWMA (bearish)
-- ---------------------------------------------------------------------------
ewma_signals AS (
    SELECT
        b.date,
        -- Price distance from EWMA (%)
        CASE WHEN e7.ewma_7d   > 0 THEN (b.gold_close - e7.ewma_7d)   / e7.ewma_7d   * 100.0 END AS price_vs_ewma_7d,
        CASE WHEN e30.ewma_30d > 0 THEN (b.gold_close - e30.ewma_30d) / e30.ewma_30d * 100.0 END AS price_vs_ewma_30d,
        CASE WHEN e90.ewma_90d > 0 THEN (b.gold_close - e90.ewma_90d) / e90.ewma_90d * 100.0 END AS price_vs_ewma_90d,
        CASE WHEN e365.ewma_365d > 0 THEN (b.gold_close - e365.ewma_365d) / e365.ewma_365d * 100.0 END AS price_vs_ewma_365d,

        -- EWMA crossover signals (short vs long):
        --   ewma_7d > ewma_30d → short-term bullish momentum
        CASE WHEN e7.ewma_7d   > e30.ewma_30d  THEN 1.0 ELSE -1.0 END AS ewma_cross_7_30,
        CASE WHEN e30.ewma_30d > e90.ewma_90d  THEN 1.0 ELSE -1.0 END AS ewma_cross_30_90,
        CASE WHEN e90.ewma_90d > e365.ewma_365d THEN 1.0 ELSE -1.0 END AS ewma_cross_90_365
    FROM base b
    LEFT JOIN ewma_7d   e7   ON b.date = e7.date
    LEFT JOIN ewma_30d  e30  ON b.date = e30.date
    LEFT JOIN ewma_90d  e90  ON b.date = e90.date
    LEFT JOIN ewma_365d e365 ON b.date = e365.date
)

-- ---------------------------------------------------------------------------
-- UPSERT vào features.ewma_features
-- ---------------------------------------------------------------------------
INSERT INTO features.ewma_features (
    date,
    -- Price EWMA
    ewma_7d,
    ewma_30d,
    ewma_90d,
    ewma_365d,
    -- Volume EWMA
    ewma_vol_7d,
    ewma_vol_30d,
    ewma_vol_90d,
    ewma_vol_365d,
    -- Signal features
    price_vs_ewma_7d,
    price_vs_ewma_30d,
    price_vs_ewma_90d,
    price_vs_ewma_365d,
    ewma_cross_7_30,
    ewma_cross_30_90,
    ewma_cross_90_365,
    updated_at
)
SELECT
    b.date,
    e7.ewma_7d,
    e30.ewma_30d,
    e90.ewma_90d,
    e365.ewma_365d,
    e7.ewma_vol_7d,
    e30.ewma_vol_30d,
    e90.ewma_vol_90d,
    e365.ewma_vol_365d,
    sig.price_vs_ewma_7d,
    sig.price_vs_ewma_30d,
    sig.price_vs_ewma_90d,
    sig.price_vs_ewma_365d,
    sig.ewma_cross_7_30,
    sig.ewma_cross_30_90,
    sig.ewma_cross_90_365,
    NOW()
FROM base b
LEFT JOIN ewma_7d       e7   ON b.date = e7.date
LEFT JOIN ewma_30d      e30  ON b.date = e30.date
LEFT JOIN ewma_90d      e90  ON b.date = e90.date
LEFT JOIN ewma_365d     e365 ON b.date = e365.date
LEFT JOIN ewma_signals  sig  ON b.date = sig.date
ON CONFLICT (date) DO UPDATE SET
    ewma_7d             = EXCLUDED.ewma_7d,
    ewma_30d            = EXCLUDED.ewma_30d,
    ewma_90d            = EXCLUDED.ewma_90d,
    ewma_365d           = EXCLUDED.ewma_365d,
    ewma_vol_7d         = EXCLUDED.ewma_vol_7d,
    ewma_vol_30d        = EXCLUDED.ewma_vol_30d,
    ewma_vol_90d        = EXCLUDED.ewma_vol_90d,
    ewma_vol_365d       = EXCLUDED.ewma_vol_365d,
    price_vs_ewma_7d    = EXCLUDED.price_vs_ewma_7d,
    price_vs_ewma_30d   = EXCLUDED.price_vs_ewma_30d,
    price_vs_ewma_90d   = EXCLUDED.price_vs_ewma_90d,
    price_vs_ewma_365d  = EXCLUDED.price_vs_ewma_365d,
    ewma_cross_7_30     = EXCLUDED.ewma_cross_7_30,
    ewma_cross_30_90    = EXCLUDED.ewma_cross_30_90,
    ewma_cross_90_365   = EXCLUDED.ewma_cross_90_365,
    updated_at          = NOW();
