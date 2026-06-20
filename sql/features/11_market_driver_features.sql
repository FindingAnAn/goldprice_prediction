-- Economically interpretable and point-in-time-safe market driver features.

WITH cot_base AS (
    SELECT
        report_date,
        available_date,
        open_interest,
        managed_money_long,
        managed_money_short,
        managed_money_long_change,
        managed_money_short_change,
        producer_long,
        producer_short,
        swap_long,
        swap_short,
        CASE WHEN open_interest > 0 THEN
            100.0 * (managed_money_long - managed_money_short) / open_interest
        END AS mm_net_pct_oi
    FROM raw.cftc_gold_positioning
    WHERE contract_code = '088691'
),
cot_windowed AS (
    SELECT
        *,
        AVG(mm_net_pct_oi) OVER (
            ORDER BY report_date ROWS BETWEEN 51 PRECEDING AND CURRENT ROW
        ) AS mm_net_avg_52w,
        STDDEV_SAMP(mm_net_pct_oi) OVER (
            ORDER BY report_date ROWS BETWEEN 51 PRECEDING AND CURRENT ROW
        ) AS mm_net_std_52w
    FROM cot_base
),
epu_intervals AS (
    SELECT
        date + 1 AS available_date,
        LEAD(date + 1) OVER (ORDER BY date) AS next_available_date,
        value
    FROM raw.fred_daily
    WHERE series_id = 'USEPUINDXD'
),
credit_intervals AS (
    SELECT
        date + 1 AS available_date,
        LEAD(date + 1) OVER (ORDER BY date) AS next_available_date,
        value
    FROM raw.fred_daily
    WHERE series_id = 'BAMLH0A0HYM2'
),
real_yield_intervals AS (
    SELECT
        date + 1 AS available_date,
        LEAD(date + 1) OVER (ORDER BY date) AS next_available_date,
        value
    FROM raw.fred_daily
    WHERE series_id = 'DFII10'
),
cot_intervals AS (
    SELECT
        *,
        LEAD(available_date) OVER (ORDER BY available_date)
            AS next_available_date
    FROM cot_windowed
),
joined AS (
    SELECT
        s.date,
        s.gold_open,
        s.gold_high,
        s.gold_low,
        s.gold_close,
        s.dxy_close,
        COALESCE(
            ry.value,
            s.us_10y_yield - s.breakeven_inflation
        ) AS real_yield,
        s.vix,
        s.sp500_close,
        gld.close AS gld_close,
        gld.volume AS gld_volume,
        tlt.close AS tlt_close,
        uup.close AS uup_close,
        tip.close AS tip_close,
        hyg.close AS hyg_close,
        epu.value AS economic_policy_uncertainty,
        credit.value AS high_yield_spread,
        cot.available_date AS cftc_available_date,
        cot.open_interest AS cftc_open_interest,
        cot.managed_money_long,
        cot.managed_money_short,
        cot.managed_money_long_change,
        cot.managed_money_short_change,
        cot.producer_long,
        cot.producer_short,
        cot.swap_long,
        cot.swap_short,
        cot.mm_net_pct_oi,
        cot.mm_net_avg_52w,
        cot.mm_net_std_52w
    FROM staging.daily_master s
    LEFT JOIN raw.yfinance_daily gld
        ON gld.date = s.date AND gld.ticker = 'GLD'
    LEFT JOIN raw.yfinance_daily tlt
        ON tlt.date = s.date AND tlt.ticker = 'TLT'
    LEFT JOIN raw.yfinance_daily uup
        ON uup.date = s.date AND uup.ticker = 'UUP'
    LEFT JOIN raw.yfinance_daily tip
        ON tip.date = s.date AND tip.ticker = 'TIP'
    LEFT JOIN raw.yfinance_daily hyg
        ON hyg.date = s.date AND hyg.ticker = 'HYG'
    LEFT JOIN epu_intervals epu
        ON s.date >= epu.available_date
       AND (s.date < epu.next_available_date OR epu.next_available_date IS NULL)
    LEFT JOIN credit_intervals credit
        ON s.date >= credit.available_date
       AND (
           s.date < credit.next_available_date
           OR credit.next_available_date IS NULL
       )
    LEFT JOIN real_yield_intervals ry
        ON s.date >= ry.available_date
       AND (s.date < ry.next_available_date OR ry.next_available_date IS NULL)
    LEFT JOIN cot_intervals cot
        ON s.date >= cot.available_date
       AND (s.date < cot.next_available_date OR cot.next_available_date IS NULL)
    WHERE s.gold_close IS NOT NULL
      AND s.date >= '2010-01-01'
),
windowed AS (
    SELECT
        *,
        LAG(gold_close, 1) OVER (ORDER BY date) AS previous_gold_close,
        LAG(dxy_close, 5) OVER (ORDER BY date) AS dxy_close_5d,
        LAG(real_yield, 5) OVER (ORDER BY date) AS real_yield_5d,
        LAG(vix, 5) OVER (ORDER BY date) AS vix_5d,
        LAG(sp500_close, 5) OVER (ORDER BY date) AS sp500_close_5d,
        LAG(gld_close, 5) OVER (ORDER BY date) AS gld_close_5d,
        LAG(tlt_close, 5) OVER (ORDER BY date) AS tlt_close_5d,
        LAG(uup_close, 5) OVER (ORDER BY date) AS uup_close_5d,
        LAG(tip_close, 5) OVER (ORDER BY date) AS tip_close_5d,
        LAG(hyg_close, 5) OVER (ORDER BY date) AS hyg_close_5d,
        LAG(high_yield_spread, 5) OVER (ORDER BY date)
            AS high_yield_spread_5d,
        AVG(gld_volume) OVER (
            ORDER BY date ROWS BETWEEN 20 PRECEDING AND CURRENT ROW
        ) AS gld_volume_avg_21d,
        STDDEV_SAMP(gld_volume) OVER (
            ORDER BY date ROWS BETWEEN 20 PRECEDING AND CURRENT ROW
        ) AS gld_volume_std_21d,
        AVG(economic_policy_uncertainty) OVER (
            ORDER BY date ROWS BETWEEN 62 PRECEDING AND CURRENT ROW
        ) AS epu_avg_63d,
        STDDEV_SAMP(economic_policy_uncertainty) OVER (
            ORDER BY date ROWS BETWEEN 62 PRECEDING AND CURRENT ROW
        ) AS epu_std_63d
    FROM joined
)
INSERT INTO features.market_driver_features (
    date,
    gold_gap_pct,
    gold_intraday_return_pct,
    gold_range_pct,
    gold_close_location,
    dxy_return_5d,
    us_10y_real_yield,
    real_yield_change_5d,
    vix_change_5d,
    sp500_return_5d,
    gld_return_5d,
    gld_volume_zscore_21d,
    tlt_return_5d,
    uup_return_5d,
    tip_return_5d,
    hyg_return_5d,
    economic_policy_uncertainty,
    epu_zscore_63d,
    high_yield_spread,
    high_yield_spread_change_5d,
    cftc_mm_net_pct_oi,
    cftc_mm_net_change_pct_oi,
    cftc_producer_net_pct_oi,
    cftc_swap_net_pct_oi,
    cftc_mm_net_zscore_52w,
    cftc_positioning_age_days,
    updated_at
)
SELECT
    date,
    CASE WHEN previous_gold_close > 0 THEN
        100.0 * (gold_open / previous_gold_close - 1.0)
    END,
    CASE WHEN gold_open > 0 THEN
        100.0 * (gold_close / gold_open - 1.0)
    END,
    CASE WHEN gold_open > 0 THEN
        100.0 * (gold_high - gold_low) / gold_open
    END,
    CASE WHEN gold_high > gold_low THEN
        (gold_close - gold_low) / (gold_high - gold_low)
    END,
    CASE WHEN dxy_close_5d > 0 THEN
        100.0 * (dxy_close / dxy_close_5d - 1.0)
    END,
    real_yield,
    real_yield - real_yield_5d,
    CASE WHEN vix_5d > 0 THEN 100.0 * (vix / vix_5d - 1.0) END,
    CASE WHEN sp500_close_5d > 0 THEN
        100.0 * (sp500_close / sp500_close_5d - 1.0)
    END,
    CASE WHEN gld_close_5d > 0 THEN
        100.0 * (gld_close / gld_close_5d - 1.0)
    END,
    CASE WHEN gld_volume_std_21d > 0 THEN
        (gld_volume - gld_volume_avg_21d) / gld_volume_std_21d
    END,
    CASE WHEN tlt_close_5d > 0 THEN
        100.0 * (tlt_close / tlt_close_5d - 1.0)
    END,
    CASE WHEN uup_close_5d > 0 THEN
        100.0 * (uup_close / uup_close_5d - 1.0)
    END,
    CASE WHEN tip_close_5d > 0 THEN
        100.0 * (tip_close / tip_close_5d - 1.0)
    END,
    CASE WHEN hyg_close_5d > 0 THEN
        100.0 * (hyg_close / hyg_close_5d - 1.0)
    END,
    economic_policy_uncertainty,
    CASE WHEN epu_std_63d > 0 THEN
        (economic_policy_uncertainty - epu_avg_63d) / epu_std_63d
    END,
    high_yield_spread,
    high_yield_spread - high_yield_spread_5d,
    mm_net_pct_oi,
    CASE WHEN cftc_open_interest > 0 THEN
        100.0
        * (managed_money_long_change - managed_money_short_change)
        / cftc_open_interest
    END,
    CASE WHEN cftc_open_interest > 0 THEN
        100.0 * (producer_long - producer_short) / cftc_open_interest
    END,
    CASE WHEN cftc_open_interest > 0 THEN
        100.0 * (swap_long - swap_short) / cftc_open_interest
    END,
    CASE WHEN mm_net_std_52w > 0 THEN
        (mm_net_pct_oi - mm_net_avg_52w) / mm_net_std_52w
    END,
    date - cftc_available_date,
    NOW()
FROM windowed
ON CONFLICT (date) DO UPDATE SET
    gold_gap_pct = EXCLUDED.gold_gap_pct,
    gold_intraday_return_pct = EXCLUDED.gold_intraday_return_pct,
    gold_range_pct = EXCLUDED.gold_range_pct,
    gold_close_location = EXCLUDED.gold_close_location,
    dxy_return_5d = EXCLUDED.dxy_return_5d,
    us_10y_real_yield = EXCLUDED.us_10y_real_yield,
    real_yield_change_5d = EXCLUDED.real_yield_change_5d,
    vix_change_5d = EXCLUDED.vix_change_5d,
    sp500_return_5d = EXCLUDED.sp500_return_5d,
    gld_return_5d = EXCLUDED.gld_return_5d,
    gld_volume_zscore_21d = EXCLUDED.gld_volume_zscore_21d,
    tlt_return_5d = EXCLUDED.tlt_return_5d,
    uup_return_5d = EXCLUDED.uup_return_5d,
    tip_return_5d = EXCLUDED.tip_return_5d,
    hyg_return_5d = EXCLUDED.hyg_return_5d,
    economic_policy_uncertainty = EXCLUDED.economic_policy_uncertainty,
    epu_zscore_63d = EXCLUDED.epu_zscore_63d,
    high_yield_spread = EXCLUDED.high_yield_spread,
    high_yield_spread_change_5d = EXCLUDED.high_yield_spread_change_5d,
    cftc_mm_net_pct_oi = EXCLUDED.cftc_mm_net_pct_oi,
    cftc_mm_net_change_pct_oi = EXCLUDED.cftc_mm_net_change_pct_oi,
    cftc_producer_net_pct_oi = EXCLUDED.cftc_producer_net_pct_oi,
    cftc_swap_net_pct_oi = EXCLUDED.cftc_swap_net_pct_oi,
    cftc_mm_net_zscore_52w = EXCLUDED.cftc_mm_net_zscore_52w,
    cftc_positioning_age_days = EXCLUDED.cftc_positioning_age_days,
    updated_at = NOW();
