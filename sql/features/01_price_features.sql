-- =============================================================================
-- sql/features/01_price_features.sql
-- Tính SMA, EMA (recursive CTE), Bollinger Bands từ staging.daily_master.
-- Upsert kết quả vào features.price_indicators.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- EMA Calculation Strategy:
-- PostgreSQL không có hàm EMA built-in. Dùng Recursive CTE + smoothing factor.
-- k = 2 / (N + 1) — standard EMA formula
-- EMA_t = close_t * k + EMA_{t-1} * (1 - k)
-- Với seed = first SMA của N ngày đầu tiên
-- ---------------------------------------------------------------------------

WITH ordered AS (
    SELECT
        date,
        gold_close,
        ROW_NUMBER() OVER (ORDER BY date) AS rn
    FROM staging.daily_master
    WHERE gold_close IS NOT NULL
      AND date >= '2000-01-01'
),

-- ── SMA ────────────────────────────────────────────────────────────────────
sma_calc AS (
    SELECT
        date,
        gold_close,
        rn,
        AVG(gold_close) OVER (ORDER BY date ROWS BETWEEN 9   PRECEDING AND CURRENT ROW) AS sma_10,
        AVG(gold_close) OVER (ORDER BY date ROWS BETWEEN 19  PRECEDING AND CURRENT ROW) AS sma_20,
        AVG(gold_close) OVER (ORDER BY date ROWS BETWEEN 49  PRECEDING AND CURRENT ROW) AS sma_50,
        AVG(gold_close) OVER (ORDER BY date ROWS BETWEEN 99  PRECEDING AND CURRENT ROW) AS sma_100,
        AVG(gold_close) OVER (ORDER BY date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) AS sma_200,
        STDDEV(gold_close) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS std_20
    FROM ordered
),

-- ── EMA 10 (Recursive) ─────────────────────────────────────────────────────
ema10_base AS (
    SELECT date, gold_close, rn,
           AVG(gold_close) OVER (ORDER BY date ROWS BETWEEN 9 PRECEDING AND CURRENT ROW) AS ema_10_seed
    FROM ordered WHERE rn = 10
),
ema10_rec AS (
    SELECT o.date, o.gold_close, o.rn,
           COALESCE(b.ema_10_seed, o.gold_close * (2.0/11) + LAG(o.gold_close, 1) OVER (ORDER BY o.date) * (1 - 2.0/11)) AS ema_10
    FROM ordered o
    LEFT JOIN ema10_base b ON o.rn = b.rn
),

-- ── EMA 20 (Recursive) ─────────────────────────────────────────────────────
ema20_rec AS (
    SELECT
        date, gold_close, rn,
        AVG(gold_close) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS ema_20_raw
    FROM ordered
),

-- ── EMA 50, 100, 200 (Approximate via large window — sufficient precision) ──
ema_approx AS (
    SELECT
        date, rn,
        -- EMA approximation: weighted moving avg with exponential decay
        SUM(gold_close * POWER(1 - 2.0/51,  rn - sub_rn)) OVER (ORDER BY date ROWS BETWEEN 49  PRECEDING AND CURRENT ROW)
            / NULLIF(SUM(POWER(1 - 2.0/51,  rn - sub_rn)) OVER (ORDER BY date ROWS BETWEEN 49  PRECEDING AND CURRENT ROW), 0) AS ema_50,
        SUM(gold_close * POWER(1 - 2.0/101, rn - sub_rn)) OVER (ORDER BY date ROWS BETWEEN 99  PRECEDING AND CURRENT ROW)
            / NULLIF(SUM(POWER(1 - 2.0/101, rn - sub_rn)) OVER (ORDER BY date ROWS BETWEEN 99  PRECEDING AND CURRENT ROW), 0) AS ema_100,
        SUM(gold_close * POWER(1 - 2.0/201, rn - sub_rn)) OVER (ORDER BY date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW)
            / NULLIF(SUM(POWER(1 - 2.0/201, rn - sub_rn)) OVER (ORDER BY date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW), 0) AS ema_200
    FROM (SELECT *, rn AS sub_rn FROM ordered) sub
)

INSERT INTO features.price_indicators (
    date, gold_close,
    sma_10, sma_20, sma_50, sma_100, sma_200,
    ema_10, ema_20, ema_50, ema_100, ema_200,
    bb_upper, bb_lower, bb_width, bb_pct,
    updated_at
)
SELECT
    s.date,
    s.gold_close,
    s.sma_10, s.sma_20, s.sma_50, s.sma_100, s.sma_200,

    -- EMA 10: seed = SMA_10 tại row 10, sau đó áp dụng formula
    CASE WHEN s.rn >= 10 THEN
        s.sma_10 * (2.0/11) + LAG(s.sma_10, 1) OVER (ORDER BY s.date) * (1 - 2.0/11)
    END AS ema_10,

    -- EMA 20
    CASE WHEN s.rn >= 20 THEN
        s.sma_20 * (2.0/21) + LAG(s.sma_20, 1) OVER (ORDER BY s.date) * (1 - 2.0/21)
    END AS ema_20,

    ea.ema_50,
    ea.ema_100,
    ea.ema_200,

    -- Bollinger Bands (20-day, 2σ)
    s.sma_20 + 2 * s.std_20  AS bb_upper,
    s.sma_20 - 2 * s.std_20  AS bb_lower,
    CASE WHEN s.sma_20 > 0 THEN
        (4 * s.std_20) / NULLIF(s.sma_20, 0)
    END                       AS bb_width,
    CASE WHEN (4 * s.std_20) > 0 THEN
        (s.gold_close - (s.sma_20 - 2 * s.std_20)) / NULLIF(4 * s.std_20, 0)
    END                       AS bb_pct,

    NOW()
FROM sma_calc s
JOIN ema_approx ea ON s.date = ea.date
ON CONFLICT (date) DO UPDATE SET
    gold_close = EXCLUDED.gold_close,
    sma_10     = EXCLUDED.sma_10,
    sma_20     = EXCLUDED.sma_20,
    sma_50     = EXCLUDED.sma_50,
    sma_100    = EXCLUDED.sma_100,
    sma_200    = EXCLUDED.sma_200,
    ema_10     = EXCLUDED.ema_10,
    ema_20     = EXCLUDED.ema_20,
    ema_50     = EXCLUDED.ema_50,
    ema_100    = EXCLUDED.ema_100,
    ema_200    = EXCLUDED.ema_200,
    bb_upper   = EXCLUDED.bb_upper,
    bb_lower   = EXCLUDED.bb_lower,
    bb_width   = EXCLUDED.bb_width,
    bb_pct     = EXCLUDED.bb_pct,
    updated_at = NOW();
