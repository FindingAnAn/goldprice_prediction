-- =============================================================================
-- sql/pipelines/run_features.sql
-- Orchestrate toàn bộ feature engineering pipeline theo thứ tự.
-- Chạy file này sau khi staging.daily_master đã được populate.
-- =============================================================================

-- Bước 1: Price Indicators (SMA, EMA, Bollinger)
\i sql/features/01_price_features.sql

-- Bước 2: Momentum Indicators (RSI, MACD, ROC, CCI, Stochastic)
\i sql/features/02_momentum_features.sql

-- Bước 3: Trend Indicators (ADX, Z-score)
\i sql/features/03_trend_features.sql

-- Bước 4: Macro Features (DXY, yields, inflation, VIX, SP500)
\i sql/features/04_macro_features.sql

-- Bước 5: Ratio Features (gold/silver, gold/oil, real yield)
\i sql/features/05_ratio_features.sql

-- Bước 6: Target Labels (TÁCH RIÊNG — không join vào master)
\i sql/features/06_target_labels.sql

-- Bước 7: Sliding Windows (5d/21d/63d/252d rolling stats)
\i sql/features/07_sliding_window.sql

-- Bước 8: EWMA Features (7d/30d/90d/365d calendar exponential weights)
\i sql/features/09_ewma_features.sql

-- Bước 9: Master Features (JOIN features + current OHLCV; không có future targets)
\i sql/features/08_master_features.sql
