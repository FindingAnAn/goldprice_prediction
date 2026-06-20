-- =============================================================================
-- sql/features/08_master_features.sql
-- Populate features.master_features = JOIN tất cả feature tables.
-- KHÔNG bao gồm features.target_labels (anti-leakage).
--
-- Prediction cutoff: after the current trading session closes.
-- Current OHLCV is therefore known and valid; only future target columns leak.
-- =============================================================================

TRUNCATE features.master_features;

INSERT INTO features.master_features (
    date,
    -- Current-session OHLCV
    gold_close, gold_open, gold_high, gold_low, gold_volume,
    -- Price Indicators
    sma_10, sma_20, sma_50, sma_100, sma_200,
    ema_10, ema_20, ema_50, ema_100, ema_200,
    bb_upper, bb_lower, bb_width, bb_pct,
    -- Momentum
    rsi_14, macd, macd_signal, macd_hist,
    roc_10, cci_20, stoch_k, stoch_d,
    -- Trend
    adx_14, plus_di, minus_di, z_score_20, z_score_60,
    -- Macro
    dxy_open, dxy_high, dxy_low, dxy_close,
    fed_funds_rate, us_interest_rate, us_10y_yield,
    us_inflation_yoy, cpi, core_cpi, breakeven_inflation,
    us_2y_yield, us_30y_yield, yield_curve_slope,
    m2_money_supply, unemployment_rate, vix, sp500_close,
    silver_close, wti_oil_price, brent_oil_price,
    -- Ratios
    gold_silver_ratio, gold_oil_ratio, gold_sp500_ratio, gold_dxy_ratio,
    real_yield, oil_spread,
    -- Sliding Windows
    gold_avg_5d,   gold_pct_chg_5d,
    gold_avg_21d,  gold_pct_chg_21d,
    gold_avg_63d,  gold_pct_chg_63d,
    gold_avg_252d, gold_pct_chg_252d,
    -- Calendar seasonality and historical analogs
    month_num, quarter_num, iso_week_num, day_of_year,
    month_sin, month_cos, year_sin, year_cos,
    month_progress, quarter_progress, year_progress, days_to_year_end,
    month_to_date_return, quarter_to_date_return, year_to_date_return,
    same_month_return_5d_mean, same_month_return_5d_std,
    same_month_up_rate_5d, same_month_samples_5d,
    same_month_return_7d_mean, same_month_up_rate_7d, same_month_samples_7d,
    same_month_return_21d_mean, same_month_up_rate_21d, same_month_samples_21d,
    same_quarter_return_21d_mean, same_quarter_up_rate_21d,
    same_quarter_samples_21d,
    same_doy_return_5d_mean, same_doy_return_5d_std,
    same_doy_up_rate_5d, same_doy_samples_5d,
    same_doy_return_7d_mean, same_doy_up_rate_7d, same_doy_samples_7d,
    same_doy_return_10d_mean, same_doy_up_rate_10d,
    same_doy_return_21d_mean, same_doy_up_rate_21d, same_doy_samples_21d,
    regime_return_5d_mean, regime_up_rate_5d, regime_samples_5d,
    regime_return_7d_mean, regime_up_rate_7d, regime_samples_7d,
    regime_return_10d_mean, regime_up_rate_10d,
    regime_return_21d_mean, regime_up_rate_21d, regime_samples_21d,
    -- EWMA Features (7d / 30d / 90d / 365d calendar)
    ewma_7d,    ewma_30d,    ewma_90d,    ewma_365d,
    ewma_vol_7d, ewma_vol_30d, ewma_vol_90d, ewma_vol_365d,
    price_vs_ewma_7d, price_vs_ewma_30d, price_vs_ewma_90d, price_vs_ewma_365d,
    ewma_cross_7_30, ewma_cross_30_90, ewma_cross_90_365,
    updated_at
)
SELECT
    s.date,
    -- Current-session OHLCV
    s.gold_close, s.gold_open, s.gold_high, s.gold_low, s.gold_volume,
    -- Price
    pi.sma_10, pi.sma_20, pi.sma_50, pi.sma_100, pi.sma_200,
    pi.ema_10, pi.ema_20, pi.ema_50, pi.ema_100, pi.ema_200,
    pi.bb_upper, pi.bb_lower, pi.bb_width, pi.bb_pct,
    -- Momentum
    mi.rsi_14, mi.macd, mi.macd_signal, mi.macd_hist,
    mi.roc_10, mi.cci_20, mi.stoch_k, mi.stoch_d,
    -- Trend
    ti.adx_14, ti.plus_di, ti.minus_di, ti.z_score_20, ti.z_score_60,
    -- Macro
    mf.dxy_open, mf.dxy_high, mf.dxy_low, mf.dxy_close,
    mf.fed_funds_rate, mf.us_interest_rate, mf.us_10y_yield,
    mf.us_inflation_yoy, mf.cpi, mf.core_cpi, mf.breakeven_inflation,
    mf.us_2y_yield, mf.us_30y_yield, mf.yield_curve_slope,
    mf.m2_money_supply, mf.unemployment_rate, mf.vix, mf.sp500_close,
    s.silver_close, s.wti_oil_price, s.brent_oil_price,
    -- Ratios
    rf.gold_silver_ratio, rf.gold_oil_ratio, rf.gold_sp500_ratio, rf.gold_dxy_ratio,
    rf.real_yield, rf.oil_spread,
    -- Sliding Windows
    sw.gold_avg_5d,   sw.gold_pct_chg_5d,
    sw.gold_avg_21d,  sw.gold_pct_chg_21d,
    sw.gold_avg_63d,  sw.gold_pct_chg_63d,
    sw.gold_avg_252d, sw.gold_pct_chg_252d,
    -- Calendar seasonality and historical analogs
    sf.month_num, sf.quarter_num, sf.iso_week_num, sf.day_of_year,
    sf.month_sin, sf.month_cos, sf.year_sin, sf.year_cos,
    sf.month_progress, sf.quarter_progress, sf.year_progress, sf.days_to_year_end,
    sf.month_to_date_return, sf.quarter_to_date_return, sf.year_to_date_return,
    sf.same_month_return_5d_mean, sf.same_month_return_5d_std,
    sf.same_month_up_rate_5d, sf.same_month_samples_5d,
    sf.same_month_return_7d_mean, sf.same_month_up_rate_7d,
    sf.same_month_samples_7d,
    sf.same_month_return_21d_mean, sf.same_month_up_rate_21d,
    sf.same_month_samples_21d,
    sf.same_quarter_return_21d_mean, sf.same_quarter_up_rate_21d,
    sf.same_quarter_samples_21d,
    sf.same_doy_return_5d_mean, sf.same_doy_return_5d_std,
    sf.same_doy_up_rate_5d, sf.same_doy_samples_5d,
    sf.same_doy_return_7d_mean, sf.same_doy_up_rate_7d,
    sf.same_doy_samples_7d,
    sf.same_doy_return_10d_mean, sf.same_doy_up_rate_10d,
    sf.same_doy_return_21d_mean, sf.same_doy_up_rate_21d,
    sf.same_doy_samples_21d,
    sf.regime_return_5d_mean, sf.regime_up_rate_5d, sf.regime_samples_5d,
    sf.regime_return_7d_mean, sf.regime_up_rate_7d, sf.regime_samples_7d,
    sf.regime_return_10d_mean, sf.regime_up_rate_10d,
    sf.regime_return_21d_mean, sf.regime_up_rate_21d, sf.regime_samples_21d,
    -- EWMA
    ew.ewma_7d,    ew.ewma_30d,    ew.ewma_90d,    ew.ewma_365d,
    ew.ewma_vol_7d, ew.ewma_vol_30d, ew.ewma_vol_90d, ew.ewma_vol_365d,
    ew.price_vs_ewma_7d, ew.price_vs_ewma_30d, ew.price_vs_ewma_90d, ew.price_vs_ewma_365d,
    ew.ewma_cross_7_30, ew.ewma_cross_30_90, ew.ewma_cross_90_365,
    NOW()
FROM staging.daily_master                 s
LEFT JOIN features.price_indicators      pi ON s.date = pi.date
LEFT JOIN features.momentum_indicators   mi ON s.date = mi.date
LEFT JOIN features.trend_indicators      ti ON s.date = ti.date
LEFT JOIN features.macro_features        mf ON s.date = mf.date
LEFT JOIN features.ratio_features        rf ON s.date = rf.date
LEFT JOIN features.sliding_windows       sw ON s.date = sw.date
LEFT JOIN features.ewma_features         ew ON s.date = ew.date
LEFT JOIN features.seasonality_features  sf ON s.date = sf.date
WHERE s.gold_close IS NOT NULL
  AND s.date >= '2000-01-01'
  AND s.is_outlier = FALSE   -- loại bỏ outlier rows
ORDER BY s.date;
