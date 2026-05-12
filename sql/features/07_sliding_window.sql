-- =============================================================================
-- sql/features/07_sliding_window.sql
-- Rolling statistics: weekly (5d), monthly (21d), quarterly (63d), yearly (252d).
-- Bao gồm avg, max, min, std, pct_change so với cùng kỳ.
-- Upsert vào features.sliding_windows.
-- =============================================================================

WITH base AS (
    SELECT
        date,
        gold_close,
        gold_volume,
        LAG(gold_close,   5) OVER (ORDER BY date)   AS close_5d_ago,
        LAG(gold_close,  21) OVER (ORDER BY date)   AS close_21d_ago,
        LAG(gold_close,  63) OVER (ORDER BY date)   AS close_63d_ago,
        LAG(gold_close, 252) OVER (ORDER BY date)   AS close_252d_ago
    FROM staging.daily_master
    WHERE gold_close IS NOT NULL
      AND date >= '2000-01-01'
)

INSERT INTO features.sliding_windows (
    date,
    -- Weekly (5 trading days)
    gold_avg_5d, gold_max_5d, gold_min_5d, gold_std_5d, gold_pct_chg_5d,
    -- Monthly (21 trading days)
    gold_avg_21d, gold_max_21d, gold_min_21d, gold_std_21d, gold_pct_chg_21d,
    -- Quarterly (63 trading days)
    gold_avg_63d, gold_max_63d, gold_min_63d, gold_std_63d, gold_pct_chg_63d,
    -- Yearly (252 trading days)
    gold_avg_252d, gold_max_252d, gold_min_252d, gold_std_252d, gold_pct_chg_252d,
    -- Volume
    volume_avg_5d, volume_avg_21d,
    updated_at
)
SELECT
    date,

    -- ── Weekly (5d) ────────────────────────────────────────────────────────
    AVG(gold_close)  OVER w5  AS gold_avg_5d,
    MAX(gold_close)  OVER w5  AS gold_max_5d,
    MIN(gold_close)  OVER w5  AS gold_min_5d,
    STDDEV(gold_close) OVER w5 AS gold_std_5d,
    CASE WHEN close_5d_ago > 0 THEN
        (gold_close - close_5d_ago) / close_5d_ago * 100.0
    END AS gold_pct_chg_5d,

    -- ── Monthly (21d) ──────────────────────────────────────────────────────
    AVG(gold_close)  OVER w21  AS gold_avg_21d,
    MAX(gold_close)  OVER w21  AS gold_max_21d,
    MIN(gold_close)  OVER w21  AS gold_min_21d,
    STDDEV(gold_close) OVER w21 AS gold_std_21d,
    CASE WHEN close_21d_ago > 0 THEN
        (gold_close - close_21d_ago) / close_21d_ago * 100.0
    END AS gold_pct_chg_21d,

    -- ── Quarterly (63d) ────────────────────────────────────────────────────
    AVG(gold_close)  OVER w63  AS gold_avg_63d,
    MAX(gold_close)  OVER w63  AS gold_max_63d,
    MIN(gold_close)  OVER w63  AS gold_min_63d,
    STDDEV(gold_close) OVER w63 AS gold_std_63d,
    CASE WHEN close_63d_ago > 0 THEN
        (gold_close - close_63d_ago) / close_63d_ago * 100.0
    END AS gold_pct_chg_63d,

    -- ── Yearly (252d) ──────────────────────────────────────────────────────
    AVG(gold_close)  OVER w252  AS gold_avg_252d,
    MAX(gold_close)  OVER w252  AS gold_max_252d,
    MIN(gold_close)  OVER w252  AS gold_min_252d,
    STDDEV(gold_close) OVER w252 AS gold_std_252d,
    CASE WHEN close_252d_ago > 0 THEN
        (gold_close - close_252d_ago) / close_252d_ago * 100.0
    END AS gold_pct_chg_252d,

    -- ── Volume Trends ──────────────────────────────────────────────────────
    AVG(gold_volume) OVER w5   AS volume_avg_5d,
    AVG(gold_volume) OVER w21  AS volume_avg_21d,

    NOW()

FROM base

WINDOW
    w5   AS (ORDER BY date ROWS BETWEEN 4   PRECEDING AND CURRENT ROW),
    w21  AS (ORDER BY date ROWS BETWEEN 20  PRECEDING AND CURRENT ROW),
    w63  AS (ORDER BY date ROWS BETWEEN 62  PRECEDING AND CURRENT ROW),
    w252 AS (ORDER BY date ROWS BETWEEN 251 PRECEDING AND CURRENT ROW)

ON CONFLICT (date) DO UPDATE SET
    gold_avg_5d        = EXCLUDED.gold_avg_5d,
    gold_max_5d        = EXCLUDED.gold_max_5d,
    gold_min_5d        = EXCLUDED.gold_min_5d,
    gold_std_5d        = EXCLUDED.gold_std_5d,
    gold_pct_chg_5d    = EXCLUDED.gold_pct_chg_5d,
    gold_avg_21d       = EXCLUDED.gold_avg_21d,
    gold_max_21d       = EXCLUDED.gold_max_21d,
    gold_min_21d       = EXCLUDED.gold_min_21d,
    gold_std_21d       = EXCLUDED.gold_std_21d,
    gold_pct_chg_21d   = EXCLUDED.gold_pct_chg_21d,
    gold_avg_63d       = EXCLUDED.gold_avg_63d,
    gold_max_63d       = EXCLUDED.gold_max_63d,
    gold_min_63d       = EXCLUDED.gold_min_63d,
    gold_std_63d       = EXCLUDED.gold_std_63d,
    gold_pct_chg_63d   = EXCLUDED.gold_pct_chg_63d,
    gold_avg_252d      = EXCLUDED.gold_avg_252d,
    gold_max_252d      = EXCLUDED.gold_max_252d,
    gold_min_252d      = EXCLUDED.gold_min_252d,
    gold_std_252d      = EXCLUDED.gold_std_252d,
    gold_pct_chg_252d  = EXCLUDED.gold_pct_chg_252d,
    volume_avg_5d      = EXCLUDED.volume_avg_5d,
    volume_avg_21d     = EXCLUDED.volume_avg_21d,
    updated_at         = NOW();
