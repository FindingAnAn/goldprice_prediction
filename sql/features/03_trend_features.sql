-- =============================================================================
-- sql/features/03_trend_features.sql
-- Tính ADX-14, Z-score (20d, 60d) từ staging.daily_master.
-- Upsert vào features.trend_indicators.
-- =============================================================================

WITH base AS (
    SELECT
        date,
        gold_close,
        gold_high,
        gold_low,
        LAG(gold_high,  1) OVER (ORDER BY date) AS prev_high,
        LAG(gold_low,   1) OVER (ORDER BY date) AS prev_low,
        LAG(gold_close, 1) OVER (ORDER BY date) AS prev_close,
        ROW_NUMBER() OVER (ORDER BY date)         AS rn
    FROM staging.daily_master
    WHERE gold_close IS NOT NULL
      AND date >= '2010-01-01'
),

-- ── True Range & Directional Movement ──────────────────────────────────────
dm_calc AS (
    SELECT
        date, rn,
        -- True Range
        GREATEST(
            gold_high - gold_low,
            ABS(gold_high - COALESCE(prev_close, gold_close)),
            ABS(gold_low  - COALESCE(prev_close, gold_close))
        ) AS tr,
        -- +DM: Upward movement
        CASE
            WHEN (gold_high - COALESCE(prev_high, gold_high)) >
                 (COALESCE(prev_low, gold_low) - gold_low)
             AND (gold_high - COALESCE(prev_high, gold_high)) > 0
            THEN  gold_high - COALESCE(prev_high, gold_high)
            ELSE 0
        END AS plus_dm,
        -- -DM: Downward movement
        CASE
            WHEN (COALESCE(prev_low, gold_low) - gold_low) >
                 (gold_high - COALESCE(prev_high, gold_high))
             AND (COALESCE(prev_low, gold_low) - gold_low) > 0
            THEN  COALESCE(prev_low, gold_low) - gold_low
            ELSE 0
        END AS minus_dm
    FROM base
    WHERE rn >= 2
),

-- ── Wilder Smoothing (14-period) ────────────────────────────────────────────
-- ATR14 = Average True Range over 14 periods
-- +DI14 = 100 * SmoothedPlusDM14 / ATR14
-- -DI14 = 100 * SmoothedMinusDM14 / ATR14
adx_components AS (
    SELECT
        date, rn,
        AVG(tr)       OVER (ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS atr_14,
        AVG(plus_dm)  OVER (ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS avg_plus_dm,
        AVG(minus_dm) OVER (ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS avg_minus_dm
    FROM dm_calc
),
di_calc AS (
    SELECT
        date, rn,
        atr_14,
        100.0 * avg_plus_dm  / NULLIF(atr_14, 0) AS plus_di,
        100.0 * avg_minus_dm / NULLIF(atr_14, 0) AS minus_di
    FROM adx_components
    WHERE rn >= 14
),

-- ── DX and ADX ──────────────────────────────────────────────────────────────
-- DX  = 100 * |+DI - -DI| / (+DI + -DI)
-- ADX = 14-period average of DX
dx_calc AS (
    SELECT
        date,
        plus_di, minus_di,
        100.0 * ABS(plus_di - minus_di) / NULLIF(plus_di + minus_di, 0) AS dx
    FROM di_calc
),
adx_calc AS (
    SELECT
        date,
        plus_di,
        minus_di,
        AVG(dx) OVER (ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS adx_14
    FROM dx_calc
),

-- ── Z-Score ─────────────────────────────────────────────────────────────────
zscore_calc AS (
    SELECT
        date,
        (gold_close - AVG(gold_close)    OVER (ORDER BY date ROWS BETWEEN 19  PRECEDING AND CURRENT ROW))
            / NULLIF(STDDEV(gold_close)  OVER (ORDER BY date ROWS BETWEEN 19  PRECEDING AND CURRENT ROW), 0)
        AS z_score_20,
        (gold_close - AVG(gold_close)    OVER (ORDER BY date ROWS BETWEEN 59  PRECEDING AND CURRENT ROW))
            / NULLIF(STDDEV(gold_close)  OVER (ORDER BY date ROWS BETWEEN 59  PRECEDING AND CURRENT ROW), 0)
        AS z_score_60
    FROM base
)

INSERT INTO features.trend_indicators (
    date,
    adx_14, plus_di, minus_di,
    z_score_20, z_score_60,
    updated_at
)
SELECT
    z.date,
    a.adx_14,
    a.plus_di,
    a.minus_di,
    z.z_score_20,
    z.z_score_60,
    NOW()
FROM zscore_calc z
LEFT JOIN adx_calc a ON z.date = a.date
ON CONFLICT (date) DO UPDATE SET
    adx_14     = EXCLUDED.adx_14,
    plus_di    = EXCLUDED.plus_di,
    minus_di   = EXCLUDED.minus_di,
    z_score_20 = EXCLUDED.z_score_20,
    z_score_60 = EXCLUDED.z_score_60,
    updated_at = NOW();
