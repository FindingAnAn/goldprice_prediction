-- =============================================================================
-- sql/features/04_macro_features.sql
-- Populate features.macro_features từ staging.daily_master.
-- Bao gồm: DXY OHLC, lãi suất, lạm phát, yield curve, VIX, SP500.
-- =============================================================================

INSERT INTO features.macro_features (
    date,
    dxy_open, dxy_high, dxy_low, dxy_close,
    fed_funds_rate,
    us_interest_rate,
    us_10y_yield,
    us_inflation_yoy,
    cpi, core_cpi,
    breakeven_inflation,
    us_2y_yield, us_30y_yield,
    yield_curve_slope,
    m2_money_supply,
    unemployment_rate,
    vix, sp500_close,
    updated_at
)
SELECT
    date,
    dxy_open, dxy_high, dxy_low, dxy_close,
    fed_funds_rate,
    us_interest_rate,   -- usintr
    us_10y_yield,
    us_inflation_yoy,   -- usiryy
    cpi, core_cpi,
    breakeven_inflation,
    us_2y_yield, us_30y_yield,
    -- Yield curve slope: fallback sang (10Y - 2Y) nếu T10Y2Y thiếu
    COALESCE(yield_curve_slope, us_10y_yield - us_2y_yield) AS yield_curve_slope,
    m2_money_supply,
    unemployment_rate,
    vix, sp500_close,
    NOW()
FROM staging.daily_master
WHERE gold_close IS NOT NULL
  AND date >= '2000-01-01'
ON CONFLICT (date) DO UPDATE SET
    dxy_open            = EXCLUDED.dxy_open,
    dxy_high            = EXCLUDED.dxy_high,
    dxy_low             = EXCLUDED.dxy_low,
    dxy_close           = EXCLUDED.dxy_close,
    fed_funds_rate      = EXCLUDED.fed_funds_rate,
    us_interest_rate    = EXCLUDED.us_interest_rate,
    us_10y_yield        = EXCLUDED.us_10y_yield,
    us_inflation_yoy    = EXCLUDED.us_inflation_yoy,
    cpi                 = EXCLUDED.cpi,
    core_cpi            = EXCLUDED.core_cpi,
    breakeven_inflation = EXCLUDED.breakeven_inflation,
    us_2y_yield         = EXCLUDED.us_2y_yield,
    us_30y_yield        = EXCLUDED.us_30y_yield,
    yield_curve_slope   = EXCLUDED.yield_curve_slope,
    m2_money_supply     = EXCLUDED.m2_money_supply,
    unemployment_rate   = EXCLUDED.unemployment_rate,
    vix                 = EXCLUDED.vix,
    sp500_close         = EXCLUDED.sp500_close,
    updated_at          = NOW();
