-- =============================================================================
-- sql/features/05_ratio_features.sql
-- Tính các tỉ lệ giá vàng so với các tài sản khác.
-- Upsert vào features.ratio_features.
-- =============================================================================

INSERT INTO features.ratio_features (
    date,
    gold_silver_ratio,
    gold_oil_ratio,
    gold_sp500_ratio,
    gold_dxy_ratio,
    real_yield,
    oil_spread,
    updated_at
)
SELECT
    date,

    -- Gold / Silver ratio (cao → vàng đắt tương đối so với bạc)
    CASE WHEN silver_close > 0 THEN
        gold_close / silver_close
    END AS gold_silver_ratio,

    -- Gold / WTI Oil ratio
    CASE WHEN wti_oil_price > 0 THEN
        gold_close / wti_oil_price
    END AS gold_oil_ratio,

    -- Gold / S&P 500 ratio
    CASE WHEN sp500_close > 0 THEN
        gold_close / sp500_close
    END AS gold_sp500_ratio,

    -- Gold / DXY ratio (nghịch chiều: DXY tăng → gold thường giảm)
    CASE WHEN dxy_close > 0 THEN
        gold_close / dxy_close
    END AS gold_dxy_ratio,

    -- Real Yield = Nominal 10Y Yield - Breakeven Inflation
    -- (real yield âm → gold tăng vì opportunity cost giảm)
    COALESCE(us_10y_yield, 0) - COALESCE(breakeven_inflation, 0)  AS real_yield,

    -- Brent-WTI spread (quality / location premium)
    brent_oil_price - wti_oil_price  AS oil_spread,

    NOW()
FROM staging.daily_master
WHERE gold_close IS NOT NULL
  AND date >= '2000-01-01'
ON CONFLICT (date) DO UPDATE SET
    gold_silver_ratio = EXCLUDED.gold_silver_ratio,
    gold_oil_ratio    = EXCLUDED.gold_oil_ratio,
    gold_sp500_ratio  = EXCLUDED.gold_sp500_ratio,
    gold_dxy_ratio    = EXCLUDED.gold_dxy_ratio,
    real_yield        = EXCLUDED.real_yield,
    oil_spread        = EXCLUDED.oil_spread,
    updated_at        = NOW();
