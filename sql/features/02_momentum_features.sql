-- =============================================================================
-- sql/features/02_momentum_features.sql
-- Tính RSI-14, MACD (12/26/9), ROC-10, CCI-20, Stochastic từ staging.
-- Upsert vào features.momentum_indicators.
-- =============================================================================

WITH base AS (
    SELECT
        date,
        gold_close,
        gold_high,
        gold_low,
        ROW_NUMBER() OVER (ORDER BY date) AS rn,
        gold_close - LAG(gold_close, 1) OVER (ORDER BY date) AS daily_change
    FROM staging.daily_master
    WHERE gold_close IS NOT NULL
      AND date >= '2000-01-01'
),

-- ── RSI-14 ─────────────────────────────────────────────────────────────────
-- Wilder's RSI: Average Gain / Average Loss over 14 periods
rsi_components AS (
    SELECT
        date,
        gold_close,
        rn,
        daily_change,
        GREATEST(daily_change, 0) AS gain,
        GREATEST(-daily_change, 0) AS loss
    FROM base
),
rsi_avgs AS (
    SELECT
        date,
        rn,
        AVG(gain) OVER (ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS avg_gain_14,
        AVG(loss) OVER (ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS avg_loss_14
    FROM rsi_components
),
rsi_calc AS (
    SELECT
        date,
        CASE
            WHEN avg_loss_14 = 0 THEN 100.0
            ELSE 100.0 - (100.0 / (1.0 + avg_gain_14 / NULLIF(avg_loss_14, 0)))
        END AS rsi_14
    FROM rsi_avgs
    WHERE rn >= 14
),

-- ── MACD (EMA12 - EMA26, Signal = EMA9 of MACD) ───────────────────────────
-- EMA approximation: weighted sum / sum of weights (LWMA approach)
ema_calc AS (
    SELECT
        date,
        gold_close,
        rn,
        -- EMA 12
        SUM(gold_close * POWER(1 - 2.0/13, rn - sub_rn)) OVER w12
            / NULLIF(SUM(POWER(1 - 2.0/13, rn - sub_rn)) OVER w12, 0) AS ema_12,
        -- EMA 26
        SUM(gold_close * POWER(1 - 2.0/27, rn - sub_rn)) OVER w26
            / NULLIF(SUM(POWER(1 - 2.0/27, rn - sub_rn)) OVER w26, 0) AS ema_26
    FROM (SELECT *, rn AS sub_rn FROM base) sub
    WINDOW
        w12 AS (ORDER BY date ROWS BETWEEN 11 PRECEDING AND CURRENT ROW),
        w26 AS (ORDER BY date ROWS BETWEEN 25 PRECEDING AND CURRENT ROW)
),
macd_line AS (
    SELECT
        date, rn,
        ema_12, ema_26,
        ema_12 - ema_26 AS macd
    FROM ema_calc
    WHERE rn >= 26
),
macd_signal_calc AS (
    -- 9-period SMA of MACD (PostgreSQL disallows nested window functions,
    -- so we use SMA as a standard approximation of the EMA-9 signal line)
    SELECT
        date, ema_12, ema_26, macd,
        AVG(macd) OVER (ORDER BY date ROWS BETWEEN 8 PRECEDING AND CURRENT ROW) AS macd_signal
    FROM macd_line
),

-- ── ROC-10 ─────────────────────────────────────────────────────────────────
-- Rate of Change: (close_t - close_{t-10}) / close_{t-10} * 100
roc_calc AS (
    SELECT
        date,
        (gold_close - LAG(gold_close, 10) OVER (ORDER BY date))
            / NULLIF(LAG(gold_close, 10) OVER (ORDER BY date), 0) * 100.0 AS roc_10
    FROM base
),

-- ── CCI-20 ─────────────────────────────────────────────────────────────────
-- CCI = (Typical Price - SMA_TP) / (0.015 * Mean Deviation)
-- Typical Price = (high + low + close) / 3
-- Split into two CTEs to avoid nested window functions:
-- Step 1: compute tp and sma_tp_20
cci_tp AS (
    SELECT
        date,
        (gold_high + gold_low + gold_close) / 3.0 AS tp,
        AVG((gold_high + gold_low + gold_close) / 3.0)
            OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS sma_tp_20
    FROM base
    WHERE gold_high IS NOT NULL AND gold_low IS NOT NULL
),
-- Step 2: use the pre-computed sma_tp_20 (plain column) in the mean deviation window
cci_calc AS (
    SELECT
        date, tp, sma_tp_20,
        AVG(ABS(tp - sma_tp_20))
            OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS mean_dev_20
    FROM cci_tp
),
cci_final AS (
    SELECT
        date,
        CASE WHEN mean_dev_20 > 0 THEN
            (tp - sma_tp_20) / (0.015 * mean_dev_20)
        END AS cci_20
    FROM cci_calc
),

-- ── Stochastic Oscillator (14-day) ─────────────────────────────────────────
-- %K = (close - lowest_low_14) / (highest_high_14 - lowest_low_14) * 100
-- %D = 3-day SMA of %K
stoch_calc AS (
    SELECT
        date,
        100.0 * (gold_close - MIN(gold_low)  OVER (ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW))
              / NULLIF(MAX(gold_high) OVER (ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW)
                - MIN(gold_low)  OVER (ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW), 0) AS stoch_k
    FROM base
    WHERE gold_high IS NOT NULL AND gold_low IS NOT NULL
),
stoch_d_calc AS (
    SELECT
        date,
        stoch_k,
        AVG(stoch_k) OVER (ORDER BY date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS stoch_d
    FROM stoch_calc
)

-- ── Final INSERT ─────────────────────────────────────────────────────────────
INSERT INTO features.momentum_indicators (
    date,
    rsi_14,
    ema_12, ema_26, macd, macd_signal, macd_hist,
    roc_10,
    cci_20,
    stoch_k, stoch_d,
    updated_at
)
SELECT
    b.date,
    r.rsi_14,
    m.ema_12,
    m.ema_26,
    m.macd,
    m.macd_signal,
    m.macd - m.macd_signal  AS macd_hist,
    rc.roc_10,
    c.cci_20,
    s.stoch_k,
    s.stoch_d,
    NOW()
FROM base b
LEFT JOIN rsi_calc          r  ON b.date = r.date
LEFT JOIN macd_signal_calc  m  ON b.date = m.date
LEFT JOIN roc_calc          rc ON b.date = rc.date
LEFT JOIN cci_final         c  ON b.date = c.date
LEFT JOIN stoch_d_calc      s  ON b.date = s.date
ON CONFLICT (date) DO UPDATE SET
    rsi_14      = EXCLUDED.rsi_14,
    ema_12      = EXCLUDED.ema_12,
    ema_26      = EXCLUDED.ema_26,
    macd        = EXCLUDED.macd,
    macd_signal = EXCLUDED.macd_signal,
    macd_hist   = EXCLUDED.macd_hist,
    roc_10      = EXCLUDED.roc_10,
    cci_20      = EXCLUDED.cci_20,
    stoch_k     = EXCLUDED.stoch_k,
    stoch_d     = EXCLUDED.stoch_d,
    updated_at  = NOW();
