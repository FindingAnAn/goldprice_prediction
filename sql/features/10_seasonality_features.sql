-- =============================================================================
-- Calendar seasonality and historical analog features.
--
-- Leakage rule:
--   Every analog observation must be at least one full year before the
--   current row. Its subsequent 5/10/21-session outcome was therefore known
--   long before the current prediction date.
-- =============================================================================

WITH ordered AS (
    SELECT
        date,
        gold_close,
        100.0 * (gold_close / NULLIF(LAG(gold_close, 1) OVER (ORDER BY date), 0) - 1.0)
            AS daily_return_pct,
        100.0 * (gold_close / NULLIF(LAG(gold_close, 21) OVER (ORDER BY date), 0) - 1.0)
            AS return_21d,
        100.0 * (
            LEAD(gold_close, 5) OVER (ORDER BY date) / NULLIF(gold_close, 0) - 1.0
        ) AS future_return_5d,
        100.0 * (
            LEAD(gold_close, 7) OVER (ORDER BY date) / NULLIF(gold_close, 0) - 1.0
        ) AS future_return_7d,
        100.0 * (
            LEAD(gold_close, 10) OVER (ORDER BY date) / NULLIF(gold_close, 0) - 1.0
        ) AS future_return_10d,
        100.0 * (
            LEAD(gold_close, 21) OVER (ORDER BY date) / NULLIF(gold_close, 0) - 1.0
        ) AS future_return_21d
    FROM staging.daily_master
    WHERE gold_close IS NOT NULL
      AND date >= '2000-01-01'
),
contextual AS (
    SELECT
        *,
        EXTRACT(MONTH FROM date)::INTEGER AS month_num,
        EXTRACT(QUARTER FROM date)::INTEGER AS quarter_num,
        EXTRACT(WEEK FROM date)::INTEGER AS iso_week_num,
        EXTRACT(DOY FROM date)::INTEGER AS day_of_year,
        STDDEV(daily_return_pct) OVER (
            ORDER BY date ROWS BETWEEN 20 PRECEDING AND CURRENT ROW
        ) AS volatility_21d,
        100.0 * (
            gold_close / NULLIF(
                FIRST_VALUE(gold_close) OVER (
                    PARTITION BY DATE_TRUNC('month', date)
                    ORDER BY date
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ),
                0
            ) - 1.0
        ) AS month_to_date_return,
        100.0 * (
            gold_close / NULLIF(
                FIRST_VALUE(gold_close) OVER (
                    PARTITION BY DATE_TRUNC('quarter', date)
                    ORDER BY date
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ),
                0
            ) - 1.0
        ) AS quarter_to_date_return,
        100.0 * (
            gold_close / NULLIF(
                FIRST_VALUE(gold_close) OVER (
                    PARTITION BY DATE_TRUNC('year', date)
                    ORDER BY date
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ),
                0
            ) - 1.0
        ) AS year_to_date_return
    FROM ordered
),
analogs AS (
    SELECT
        c.date,

        AVG(h.future_return_5d) FILTER (
            WHERE h.month_num = c.month_num
        ) AS same_month_return_5d_mean,
        STDDEV(h.future_return_5d) FILTER (
            WHERE h.month_num = c.month_num
        ) AS same_month_return_5d_std,
        AVG((h.future_return_5d > 0)::INTEGER::DOUBLE PRECISION) FILTER (
            WHERE h.month_num = c.month_num
        ) AS same_month_up_rate_5d,
        COUNT(h.future_return_5d) FILTER (
            WHERE h.month_num = c.month_num
        )::INTEGER AS same_month_samples_5d,

        AVG(h.future_return_7d) FILTER (
            WHERE h.month_num = c.month_num
        ) AS same_month_return_7d_mean,
        AVG((h.future_return_7d > 0)::INTEGER::DOUBLE PRECISION) FILTER (
            WHERE h.month_num = c.month_num
        ) AS same_month_up_rate_7d,
        COUNT(h.future_return_7d) FILTER (
            WHERE h.month_num = c.month_num
        )::INTEGER AS same_month_samples_7d,

        AVG(h.future_return_21d) FILTER (
            WHERE h.month_num = c.month_num
        ) AS same_month_return_21d_mean,
        AVG((h.future_return_21d > 0)::INTEGER::DOUBLE PRECISION) FILTER (
            WHERE h.month_num = c.month_num
        ) AS same_month_up_rate_21d,
        COUNT(h.future_return_21d) FILTER (
            WHERE h.month_num = c.month_num
        )::INTEGER AS same_month_samples_21d,

        AVG(h.future_return_21d) FILTER (
            WHERE h.quarter_num = c.quarter_num
        ) AS same_quarter_return_21d_mean,
        AVG((h.future_return_21d > 0)::INTEGER::DOUBLE PRECISION) FILTER (
            WHERE h.quarter_num = c.quarter_num
        ) AS same_quarter_up_rate_21d,
        COUNT(h.future_return_21d) FILTER (
            WHERE h.quarter_num = c.quarter_num
        )::INTEGER AS same_quarter_samples_21d,

        AVG(h.future_return_5d) FILTER (
            WHERE LEAST(
                ABS(h.day_of_year - c.day_of_year),
                366 - ABS(h.day_of_year - c.day_of_year)
            ) <= 10
        ) AS same_doy_return_5d_mean,
        STDDEV(h.future_return_5d) FILTER (
            WHERE LEAST(
                ABS(h.day_of_year - c.day_of_year),
                366 - ABS(h.day_of_year - c.day_of_year)
            ) <= 10
        ) AS same_doy_return_5d_std,
        AVG((h.future_return_5d > 0)::INTEGER::DOUBLE PRECISION) FILTER (
            WHERE LEAST(
                ABS(h.day_of_year - c.day_of_year),
                366 - ABS(h.day_of_year - c.day_of_year)
            ) <= 10
        ) AS same_doy_up_rate_5d,
        COUNT(h.future_return_5d) FILTER (
            WHERE LEAST(
                ABS(h.day_of_year - c.day_of_year),
                366 - ABS(h.day_of_year - c.day_of_year)
            ) <= 10
        )::INTEGER AS same_doy_samples_5d,

        AVG(h.future_return_7d) FILTER (
            WHERE LEAST(
                ABS(h.day_of_year - c.day_of_year),
                366 - ABS(h.day_of_year - c.day_of_year)
            ) <= 10
        ) AS same_doy_return_7d_mean,
        AVG((h.future_return_7d > 0)::INTEGER::DOUBLE PRECISION) FILTER (
            WHERE LEAST(
                ABS(h.day_of_year - c.day_of_year),
                366 - ABS(h.day_of_year - c.day_of_year)
            ) <= 10
        ) AS same_doy_up_rate_7d,
        COUNT(h.future_return_7d) FILTER (
            WHERE LEAST(
                ABS(h.day_of_year - c.day_of_year),
                366 - ABS(h.day_of_year - c.day_of_year)
            ) <= 10
        )::INTEGER AS same_doy_samples_7d,

        AVG(h.future_return_10d) FILTER (
            WHERE LEAST(
                ABS(h.day_of_year - c.day_of_year),
                366 - ABS(h.day_of_year - c.day_of_year)
            ) <= 10
        ) AS same_doy_return_10d_mean,
        AVG((h.future_return_10d > 0)::INTEGER::DOUBLE PRECISION) FILTER (
            WHERE LEAST(
                ABS(h.day_of_year - c.day_of_year),
                366 - ABS(h.day_of_year - c.day_of_year)
            ) <= 10
        ) AS same_doy_up_rate_10d,

        AVG(h.future_return_21d) FILTER (
            WHERE LEAST(
                ABS(h.day_of_year - c.day_of_year),
                366 - ABS(h.day_of_year - c.day_of_year)
            ) <= 10
        ) AS same_doy_return_21d_mean,
        AVG((h.future_return_21d > 0)::INTEGER::DOUBLE PRECISION) FILTER (
            WHERE LEAST(
                ABS(h.day_of_year - c.day_of_year),
                366 - ABS(h.day_of_year - c.day_of_year)
            ) <= 10
        ) AS same_doy_up_rate_21d,
        COUNT(h.future_return_21d) FILTER (
            WHERE LEAST(
                ABS(h.day_of_year - c.day_of_year),
                366 - ABS(h.day_of_year - c.day_of_year)
            ) <= 10
        )::INTEGER AS same_doy_samples_21d,

        AVG(h.future_return_5d) FILTER (
            WHERE ABS(h.return_21d - c.return_21d) <= 2.0
              AND ABS(h.volatility_21d - c.volatility_21d) <= 0.35
        ) AS regime_return_5d_mean,
        AVG((h.future_return_5d > 0)::INTEGER::DOUBLE PRECISION) FILTER (
            WHERE ABS(h.return_21d - c.return_21d) <= 2.0
              AND ABS(h.volatility_21d - c.volatility_21d) <= 0.35
        ) AS regime_up_rate_5d,
        COUNT(h.future_return_5d) FILTER (
            WHERE ABS(h.return_21d - c.return_21d) <= 2.0
              AND ABS(h.volatility_21d - c.volatility_21d) <= 0.35
        )::INTEGER AS regime_samples_5d,

        AVG(h.future_return_7d) FILTER (
            WHERE ABS(h.return_21d - c.return_21d) <= 2.0
              AND ABS(h.volatility_21d - c.volatility_21d) <= 0.35
        ) AS regime_return_7d_mean,
        AVG((h.future_return_7d > 0)::INTEGER::DOUBLE PRECISION) FILTER (
            WHERE ABS(h.return_21d - c.return_21d) <= 2.0
              AND ABS(h.volatility_21d - c.volatility_21d) <= 0.35
        ) AS regime_up_rate_7d,
        COUNT(h.future_return_7d) FILTER (
            WHERE ABS(h.return_21d - c.return_21d) <= 2.0
              AND ABS(h.volatility_21d - c.volatility_21d) <= 0.35
        )::INTEGER AS regime_samples_7d,

        AVG(h.future_return_10d) FILTER (
            WHERE ABS(h.return_21d - c.return_21d) <= 2.0
              AND ABS(h.volatility_21d - c.volatility_21d) <= 0.35
        ) AS regime_return_10d_mean,
        AVG((h.future_return_10d > 0)::INTEGER::DOUBLE PRECISION) FILTER (
            WHERE ABS(h.return_21d - c.return_21d) <= 2.0
              AND ABS(h.volatility_21d - c.volatility_21d) <= 0.35
        ) AS regime_up_rate_10d,

        AVG(h.future_return_21d) FILTER (
            WHERE ABS(h.return_21d - c.return_21d) <= 2.0
              AND ABS(h.volatility_21d - c.volatility_21d) <= 0.35
        ) AS regime_return_21d_mean,
        AVG((h.future_return_21d > 0)::INTEGER::DOUBLE PRECISION) FILTER (
            WHERE ABS(h.return_21d - c.return_21d) <= 2.0
              AND ABS(h.volatility_21d - c.volatility_21d) <= 0.35
        ) AS regime_up_rate_21d,
        COUNT(h.future_return_21d) FILTER (
            WHERE ABS(h.return_21d - c.return_21d) <= 2.0
              AND ABS(h.volatility_21d - c.volatility_21d) <= 0.35
        )::INTEGER AS regime_samples_21d
    FROM contextual c
    LEFT JOIN contextual h
      ON h.date <= (c.date - INTERVAL '1 year')::DATE
    GROUP BY c.date
)
INSERT INTO features.seasonality_features (
    date,
    month_num, quarter_num, iso_week_num, day_of_year,
    month_sin, month_cos, year_sin, year_cos,
    month_progress, quarter_progress, year_progress, days_to_year_end,
    month_to_date_return, quarter_to_date_return, year_to_date_return,
    same_month_return_5d_mean, same_month_return_5d_std,
    same_month_up_rate_5d, same_month_samples_5d,
    same_month_return_7d_mean, same_month_up_rate_7d, same_month_samples_7d,
    same_month_return_21d_mean, same_month_up_rate_21d, same_month_samples_21d,
    same_quarter_return_21d_mean, same_quarter_up_rate_21d, same_quarter_samples_21d,
    same_doy_return_5d_mean, same_doy_return_5d_std,
    same_doy_up_rate_5d, same_doy_samples_5d,
    same_doy_return_7d_mean, same_doy_up_rate_7d, same_doy_samples_7d,
    same_doy_return_10d_mean, same_doy_up_rate_10d,
    same_doy_return_21d_mean, same_doy_up_rate_21d, same_doy_samples_21d,
    regime_return_5d_mean, regime_up_rate_5d, regime_samples_5d,
    regime_return_7d_mean, regime_up_rate_7d, regime_samples_7d,
    regime_return_10d_mean, regime_up_rate_10d,
    regime_return_21d_mean, regime_up_rate_21d, regime_samples_21d,
    updated_at
)
SELECT
    c.date,
    c.month_num,
    c.quarter_num,
    c.iso_week_num,
    c.day_of_year,
    SIN(2.0 * PI() * c.month_num / 12.0),
    COS(2.0 * PI() * c.month_num / 12.0),
    SIN(2.0 * PI() * c.day_of_year / 365.25),
    COS(2.0 * PI() * c.day_of_year / 365.25),
    (EXTRACT(DAY FROM c.date) - 1.0)
        / NULLIF(EXTRACT(DAY FROM (DATE_TRUNC('month', c.date) + INTERVAL '1 month - 1 day')), 0),
    (c.date - DATE_TRUNC('quarter', c.date)::DATE)::DOUBLE PRECISION
        / NULLIF(
            (
                (DATE_TRUNC('quarter', c.date) + INTERVAL '3 months')::DATE
                - DATE_TRUNC('quarter', c.date)::DATE
            )::DOUBLE PRECISION,
            0
        ),
    (c.day_of_year - 1.0) / 365.25,
    (DATE_TRUNC('year', c.date) + INTERVAL '1 year')::DATE - c.date,
    c.month_to_date_return,
    c.quarter_to_date_return,
    c.year_to_date_return,
    a.same_month_return_5d_mean,
    a.same_month_return_5d_std,
    a.same_month_up_rate_5d,
    a.same_month_samples_5d,
    a.same_month_return_7d_mean,
    a.same_month_up_rate_7d,
    a.same_month_samples_7d,
    a.same_month_return_21d_mean,
    a.same_month_up_rate_21d,
    a.same_month_samples_21d,
    a.same_quarter_return_21d_mean,
    a.same_quarter_up_rate_21d,
    a.same_quarter_samples_21d,
    a.same_doy_return_5d_mean,
    a.same_doy_return_5d_std,
    a.same_doy_up_rate_5d,
    a.same_doy_samples_5d,
    a.same_doy_return_7d_mean,
    a.same_doy_up_rate_7d,
    a.same_doy_samples_7d,
    a.same_doy_return_10d_mean,
    a.same_doy_up_rate_10d,
    a.same_doy_return_21d_mean,
    a.same_doy_up_rate_21d,
    a.same_doy_samples_21d,
    a.regime_return_5d_mean,
    a.regime_up_rate_5d,
    a.regime_samples_5d,
    a.regime_return_7d_mean,
    a.regime_up_rate_7d,
    a.regime_samples_7d,
    a.regime_return_10d_mean,
    a.regime_up_rate_10d,
    a.regime_return_21d_mean,
    a.regime_up_rate_21d,
    a.regime_samples_21d,
    NOW()
FROM contextual c
LEFT JOIN analogs a ON c.date = a.date
ON CONFLICT (date) DO UPDATE SET
    month_num = EXCLUDED.month_num,
    quarter_num = EXCLUDED.quarter_num,
    iso_week_num = EXCLUDED.iso_week_num,
    day_of_year = EXCLUDED.day_of_year,
    month_sin = EXCLUDED.month_sin,
    month_cos = EXCLUDED.month_cos,
    year_sin = EXCLUDED.year_sin,
    year_cos = EXCLUDED.year_cos,
    month_progress = EXCLUDED.month_progress,
    quarter_progress = EXCLUDED.quarter_progress,
    year_progress = EXCLUDED.year_progress,
    days_to_year_end = EXCLUDED.days_to_year_end,
    month_to_date_return = EXCLUDED.month_to_date_return,
    quarter_to_date_return = EXCLUDED.quarter_to_date_return,
    year_to_date_return = EXCLUDED.year_to_date_return,
    same_month_return_5d_mean = EXCLUDED.same_month_return_5d_mean,
    same_month_return_5d_std = EXCLUDED.same_month_return_5d_std,
    same_month_up_rate_5d = EXCLUDED.same_month_up_rate_5d,
    same_month_samples_5d = EXCLUDED.same_month_samples_5d,
    same_month_return_7d_mean = EXCLUDED.same_month_return_7d_mean,
    same_month_up_rate_7d = EXCLUDED.same_month_up_rate_7d,
    same_month_samples_7d = EXCLUDED.same_month_samples_7d,
    same_month_return_21d_mean = EXCLUDED.same_month_return_21d_mean,
    same_month_up_rate_21d = EXCLUDED.same_month_up_rate_21d,
    same_month_samples_21d = EXCLUDED.same_month_samples_21d,
    same_quarter_return_21d_mean = EXCLUDED.same_quarter_return_21d_mean,
    same_quarter_up_rate_21d = EXCLUDED.same_quarter_up_rate_21d,
    same_quarter_samples_21d = EXCLUDED.same_quarter_samples_21d,
    same_doy_return_5d_mean = EXCLUDED.same_doy_return_5d_mean,
    same_doy_return_5d_std = EXCLUDED.same_doy_return_5d_std,
    same_doy_up_rate_5d = EXCLUDED.same_doy_up_rate_5d,
    same_doy_samples_5d = EXCLUDED.same_doy_samples_5d,
    same_doy_return_7d_mean = EXCLUDED.same_doy_return_7d_mean,
    same_doy_up_rate_7d = EXCLUDED.same_doy_up_rate_7d,
    same_doy_samples_7d = EXCLUDED.same_doy_samples_7d,
    same_doy_return_10d_mean = EXCLUDED.same_doy_return_10d_mean,
    same_doy_up_rate_10d = EXCLUDED.same_doy_up_rate_10d,
    same_doy_return_21d_mean = EXCLUDED.same_doy_return_21d_mean,
    same_doy_up_rate_21d = EXCLUDED.same_doy_up_rate_21d,
    same_doy_samples_21d = EXCLUDED.same_doy_samples_21d,
    regime_return_5d_mean = EXCLUDED.regime_return_5d_mean,
    regime_up_rate_5d = EXCLUDED.regime_up_rate_5d,
    regime_samples_5d = EXCLUDED.regime_samples_5d,
    regime_return_7d_mean = EXCLUDED.regime_return_7d_mean,
    regime_up_rate_7d = EXCLUDED.regime_up_rate_7d,
    regime_samples_7d = EXCLUDED.regime_samples_7d,
    regime_return_10d_mean = EXCLUDED.regime_return_10d_mean,
    regime_up_rate_10d = EXCLUDED.regime_up_rate_10d,
    regime_return_21d_mean = EXCLUDED.regime_return_21d_mean,
    regime_up_rate_21d = EXCLUDED.regime_up_rate_21d,
    regime_samples_21d = EXCLUDED.regime_samples_21d,
    updated_at = NOW();
