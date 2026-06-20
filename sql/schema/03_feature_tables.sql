-- =============================================================================
-- sql/schema/03_feature_tables.sql
-- Tạo các bảng trong schema features (SQL-computed indicators).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- features.price_indicators
-- SMA, EMA, Bollinger Bands
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS features.price_indicators (
    date        DATE             NOT NULL PRIMARY KEY,
    gold_close  DOUBLE PRECISION,

    -- Simple Moving Averages
    sma_10      DOUBLE PRECISION,
    sma_20      DOUBLE PRECISION,
    sma_50      DOUBLE PRECISION,
    sma_100     DOUBLE PRECISION,
    sma_200     DOUBLE PRECISION,

    -- Exponential Moving Averages
    ema_10      DOUBLE PRECISION,
    ema_20      DOUBLE PRECISION,
    ema_50      DOUBLE PRECISION,
    ema_100     DOUBLE PRECISION,
    ema_200     DOUBLE PRECISION,

    -- Bollinger Bands (20-day, 2 std)
    bb_upper    DOUBLE PRECISION,
    bb_lower    DOUBLE PRECISION,
    bb_width    DOUBLE PRECISION,   -- (upper - lower) / sma_20
    bb_pct      DOUBLE PRECISION,   -- (close - lower) / (upper - lower)

    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- features.momentum_indicators
-- RSI, MACD, ROC, CCI
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS features.momentum_indicators (
    date            DATE             NOT NULL PRIMARY KEY,

    -- RSI (14-day)
    rsi_14          DOUBLE PRECISION,

    -- MACD (12, 26, 9)
    ema_12          DOUBLE PRECISION,
    ema_26          DOUBLE PRECISION,
    macd            DOUBLE PRECISION,   -- ema_12 - ema_26
    macd_signal     DOUBLE PRECISION,   -- EMA_9(macd)
    macd_hist       DOUBLE PRECISION,   -- macd - macd_signal

    -- Rate of Change
    roc_10          DOUBLE PRECISION,   -- (close_t - close_{t-10}) / close_{t-10} * 100

    -- Commodity Channel Index (20-day)
    cci_20          DOUBLE PRECISION,

    -- Stochastic Oscillator (14-day)
    stoch_k         DOUBLE PRECISION,
    stoch_d         DOUBLE PRECISION,

    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- features.trend_indicators
-- ADX, Z-score
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS features.trend_indicators (
    date            DATE             NOT NULL PRIMARY KEY,

    -- Average Directional Index (14-day)
    adx_14          DOUBLE PRECISION,
    plus_di         DOUBLE PRECISION,   -- +DI
    minus_di        DOUBLE PRECISION,   -- -DI

    -- Z-score (20-day rolling)
    z_score_20      DOUBLE PRECISION,

    -- Z-score (60-day rolling)
    z_score_60      DOUBLE PRECISION,

    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- features.macro_features
-- DXY OHLC, Fed Funds, yields and inflation
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS features.macro_features (
    date                DATE             NOT NULL PRIMARY KEY,

    -- DXY (US Dollar Index OHLC) — từ raw.yfinance_daily ticker='DX-Y.NYB'
    dxy_open            DOUBLE PRECISION,
    dxy_high            DOUBLE PRECISION,
    dxy_low             DOUBLE PRECISION,
    dxy_close           DOUBLE PRECISION,

    -- Interest Rates
    fed_funds_rate      DOUBLE PRECISION,   -- FEDFUNDS (monthly, forward-filled)
    us_10y_yield        DOUBLE PRECISION,   -- DGS10

    -- Inflation
    cpi                 DOUBLE PRECISION,   -- CPIAUCSL
    core_cpi            DOUBLE PRECISION,   -- CPILFESL
    breakeven_inflation DOUBLE PRECISION,   -- T10YIE

    -- Yield Curve
    us_2y_yield         DOUBLE PRECISION,
    us_30y_yield        DOUBLE PRECISION,
    yield_curve_slope   DOUBLE PRECISION,   -- T10Y2Y (10Y - 2Y)

    -- Money Supply
    m2_money_supply     DOUBLE PRECISION,

    -- Labor
    unemployment_rate   DOUBLE PRECISION,

    -- Equity Sentiment
    vix                 DOUBLE PRECISION,
    sp500_close         DOUBLE PRECISION,

    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- features.ratio_features
-- Gold/silver, gold/oil, yield curve ratios
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS features.ratio_features (
    date                DATE             NOT NULL PRIMARY KEY,

    gold_silver_ratio   DOUBLE PRECISION,   -- gold_close / silver_close
    gold_oil_ratio      DOUBLE PRECISION,   -- gold_close / wti_oil_price
    gold_sp500_ratio    DOUBLE PRECISION,   -- gold_close / sp500_close
    gold_dxy_ratio      DOUBLE PRECISION,   -- gold_close / dxy_close
    real_yield          DOUBLE PRECISION,   -- us_10y_yield - breakeven_inflation

    -- Spread
    oil_spread          DOUBLE PRECISION,   -- brent_oil_price - wti_oil_price

    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- features.market_driver_features
-- Economically interpretable market, uncertainty, credit and positioning
-- features. All external observations are joined by their known availability.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS features.market_driver_features (
    date                              DATE NOT NULL PRIMARY KEY,
    gold_gap_pct                      DOUBLE PRECISION,
    gold_intraday_return_pct          DOUBLE PRECISION,
    gold_range_pct                    DOUBLE PRECISION,
    gold_close_location               DOUBLE PRECISION,
    dxy_return_5d                     DOUBLE PRECISION,
    us_10y_real_yield                DOUBLE PRECISION,
    real_yield_change_5d              DOUBLE PRECISION,
    vix_change_5d                     DOUBLE PRECISION,
    sp500_return_5d                   DOUBLE PRECISION,
    gld_return_5d                     DOUBLE PRECISION,
    gld_volume_zscore_21d             DOUBLE PRECISION,
    tlt_return_5d                     DOUBLE PRECISION,
    uup_return_5d                     DOUBLE PRECISION,
    tip_return_5d                     DOUBLE PRECISION,
    hyg_return_5d                     DOUBLE PRECISION,
    economic_policy_uncertainty       DOUBLE PRECISION,
    epu_zscore_63d                    DOUBLE PRECISION,
    high_yield_spread                 DOUBLE PRECISION,
    high_yield_spread_change_5d       DOUBLE PRECISION,
    cftc_mm_net_pct_oi                DOUBLE PRECISION,
    cftc_mm_net_change_pct_oi         DOUBLE PRECISION,
    cftc_producer_net_pct_oi          DOUBLE PRECISION,
    cftc_swap_net_pct_oi              DOUBLE PRECISION,
    cftc_mm_net_zscore_52w            DOUBLE PRECISION,
    cftc_positioning_age_days         INTEGER,
    updated_at                        TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE features.market_driver_features
    ADD COLUMN IF NOT EXISTS us_10y_real_yield DOUBLE PRECISION;

-- ---------------------------------------------------------------------------
-- features.sliding_windows
-- Rolling stats: weekly/monthly/quarterly/yearly
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS features.sliding_windows (
    date                    DATE             NOT NULL PRIMARY KEY,

    -- Weekly (5 trading days)
    gold_avg_5d             DOUBLE PRECISION,
    gold_max_5d             DOUBLE PRECISION,
    gold_min_5d             DOUBLE PRECISION,
    gold_std_5d             DOUBLE PRECISION,
    gold_pct_chg_5d         DOUBLE PRECISION,

    -- Monthly (21 trading days)
    gold_avg_21d            DOUBLE PRECISION,
    gold_max_21d            DOUBLE PRECISION,
    gold_min_21d            DOUBLE PRECISION,
    gold_std_21d            DOUBLE PRECISION,
    gold_pct_chg_21d        DOUBLE PRECISION,

    -- Quarterly (63 trading days)
    gold_avg_63d            DOUBLE PRECISION,
    gold_max_63d            DOUBLE PRECISION,
    gold_min_63d            DOUBLE PRECISION,
    gold_std_63d            DOUBLE PRECISION,
    gold_pct_chg_63d        DOUBLE PRECISION,

    -- Yearly (252 trading days)
    gold_avg_252d           DOUBLE PRECISION,
    gold_max_252d           DOUBLE PRECISION,
    gold_min_252d           DOUBLE PRECISION,
    gold_std_252d           DOUBLE PRECISION,
    gold_pct_chg_252d       DOUBLE PRECISION,

    -- Volume trends
    volume_avg_5d           DOUBLE PRECISION,
    volume_avg_21d          DOUBLE PRECISION,

    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- features.seasonality_features
-- Calendar position plus leakage-safe analog outcomes from prior years.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS features.seasonality_features (
    date                            DATE NOT NULL PRIMARY KEY,
    month_num                       INTEGER,
    quarter_num                     INTEGER,
    iso_week_num                    INTEGER,
    day_of_year                     INTEGER,
    month_sin                       DOUBLE PRECISION,
    month_cos                       DOUBLE PRECISION,
    year_sin                        DOUBLE PRECISION,
    year_cos                        DOUBLE PRECISION,
    month_progress                  DOUBLE PRECISION,
    quarter_progress                DOUBLE PRECISION,
    year_progress                   DOUBLE PRECISION,
    days_to_year_end                INTEGER,
    month_to_date_return            DOUBLE PRECISION,
    quarter_to_date_return          DOUBLE PRECISION,
    year_to_date_return             DOUBLE PRECISION,
    same_month_return_5d_mean       DOUBLE PRECISION,
    same_month_return_5d_std        DOUBLE PRECISION,
    same_month_up_rate_5d           DOUBLE PRECISION,
    same_month_samples_5d           INTEGER,
    same_month_return_7d_mean       DOUBLE PRECISION,
    same_month_up_rate_7d           DOUBLE PRECISION,
    same_month_samples_7d           INTEGER,
    same_month_return_21d_mean      DOUBLE PRECISION,
    same_month_up_rate_21d          DOUBLE PRECISION,
    same_month_samples_21d          INTEGER,
    same_quarter_return_21d_mean    DOUBLE PRECISION,
    same_quarter_up_rate_21d        DOUBLE PRECISION,
    same_quarter_samples_21d        INTEGER,
    same_doy_return_5d_mean         DOUBLE PRECISION,
    same_doy_return_5d_std          DOUBLE PRECISION,
    same_doy_up_rate_5d             DOUBLE PRECISION,
    same_doy_samples_5d             INTEGER,
    same_doy_return_7d_mean         DOUBLE PRECISION,
    same_doy_up_rate_7d             DOUBLE PRECISION,
    same_doy_samples_7d             INTEGER,
    same_doy_return_10d_mean        DOUBLE PRECISION,
    same_doy_up_rate_10d            DOUBLE PRECISION,
    same_doy_return_21d_mean        DOUBLE PRECISION,
    same_doy_up_rate_21d            DOUBLE PRECISION,
    same_doy_samples_21d            INTEGER,
    regime_return_5d_mean           DOUBLE PRECISION,
    regime_up_rate_5d               DOUBLE PRECISION,
    regime_samples_5d               INTEGER,
    regime_return_7d_mean           DOUBLE PRECISION,
    regime_up_rate_7d               DOUBLE PRECISION,
    regime_samples_7d               INTEGER,
    regime_return_10d_mean          DOUBLE PRECISION,
    regime_up_rate_10d              DOUBLE PRECISION,
    regime_return_21d_mean          DOUBLE PRECISION,
    regime_up_rate_21d              DOUBLE PRECISION,
    regime_samples_21d              INTEGER,
    updated_at                      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE features.seasonality_features
    ADD COLUMN IF NOT EXISTS same_month_return_7d_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS same_month_up_rate_7d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS same_month_samples_7d INTEGER,
    ADD COLUMN IF NOT EXISTS same_doy_return_7d_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS same_doy_up_rate_7d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS same_doy_samples_7d INTEGER,
    ADD COLUMN IF NOT EXISTS regime_return_7d_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS regime_up_rate_7d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS regime_samples_7d INTEGER;

-- ---------------------------------------------------------------------------
-- features.ewma_features
-- Exponential Weighted Moving Average: 7d, 30d, 90d, 365d (calendar days)
-- alpha = 2 / (span + 1) với span ≈ trading days
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS features.ewma_features (
    date                DATE             NOT NULL PRIMARY KEY,

    -- EWMA Price (calendar day windows → trading day span)
    ewma_7d             DOUBLE PRECISION,   -- span=5,  alpha=2/6
    ewma_30d            DOUBLE PRECISION,   -- span=21, alpha=2/22
    ewma_90d            DOUBLE PRECISION,   -- span=63, alpha=2/64
    ewma_365d           DOUBLE PRECISION,   -- span=252, alpha=2/253

    -- EWMA Volume
    ewma_vol_7d         DOUBLE PRECISION,
    ewma_vol_30d        DOUBLE PRECISION,
    ewma_vol_90d        DOUBLE PRECISION,
    ewma_vol_365d       DOUBLE PRECISION,

    -- Price vs EWMA distance (%): > 0 = bullish, < 0 = bearish
    price_vs_ewma_7d    DOUBLE PRECISION,
    price_vs_ewma_30d   DOUBLE PRECISION,
    price_vs_ewma_90d   DOUBLE PRECISION,
    price_vs_ewma_365d  DOUBLE PRECISION,

    -- EWMA Crossover signals: +1 = bullish (short > long), -1 = bearish
    ewma_cross_7_30     DOUBLE PRECISION,   -- ewma_7d  vs ewma_30d
    ewma_cross_30_90    DOUBLE PRECISION,   -- ewma_30d vs ewma_90d
    ewma_cross_90_365   DOUBLE PRECISION,   -- ewma_90d vs ewma_365d

    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- features.target_labels: isolated multi-output gold-open targets.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS features.target_labels (
    date                    DATE             NOT NULL PRIMARY KEY,

    -- Next 10 trading-session gold opens (multi-output forecast target)
    next_1_day_open         DOUBLE PRECISION,
    next_2_day_open         DOUBLE PRECISION,
    next_3_day_open         DOUBLE PRECISION,
    next_4_day_open         DOUBLE PRECISION,
    next_5_day_open         DOUBLE PRECISION,
    next_6_day_open         DOUBLE PRECISION,
    next_7_day_open         DOUBLE PRECISION,
    next_8_day_open         DOUBLE PRECISION,
    next_9_day_open         DOUBLE PRECISION,
    next_10_day_open        DOUBLE PRECISION,

    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- features.master_features
-- JOIN tất cả features — KHÔNG chứa target labels (anti-leakage).
--
-- Anti-leakage design:
--   OHLCV phiên hiện tại: hợp lệ vì thời điểm dự báo là sau khi phiên đóng cửa.
--   next_*_day_*: KHÔNG lưu ở đây; target labels luôn nằm ở bảng riêng.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS features.master_features (
    date                DATE             NOT NULL PRIMARY KEY,

    -- Current-session OHLCV. Valid because prediction runs after market close.
    gold_close          DOUBLE PRECISION,
    gold_open           DOUBLE PRECISION,
    gold_high           DOUBLE PRECISION,
    gold_low            DOUBLE PRECISION,
    gold_volume         DOUBLE PRECISION,

    -- Price Indicators
    sma_10              DOUBLE PRECISION,
    sma_20              DOUBLE PRECISION,
    sma_50              DOUBLE PRECISION,
    sma_100             DOUBLE PRECISION,
    sma_200             DOUBLE PRECISION,
    ema_10              DOUBLE PRECISION,
    ema_20              DOUBLE PRECISION,
    ema_50              DOUBLE PRECISION,
    ema_100             DOUBLE PRECISION,
    ema_200             DOUBLE PRECISION,
    bb_upper            DOUBLE PRECISION,
    bb_lower            DOUBLE PRECISION,
    bb_width            DOUBLE PRECISION,
    bb_pct              DOUBLE PRECISION,

    -- Momentum
    rsi_14              DOUBLE PRECISION,
    macd                DOUBLE PRECISION,
    macd_signal         DOUBLE PRECISION,
    macd_hist           DOUBLE PRECISION,
    roc_10              DOUBLE PRECISION,
    cci_20              DOUBLE PRECISION,
    stoch_k             DOUBLE PRECISION,
    stoch_d             DOUBLE PRECISION,

    -- Trend
    adx_14              DOUBLE PRECISION,
    plus_di             DOUBLE PRECISION,
    minus_di            DOUBLE PRECISION,
    z_score_20          DOUBLE PRECISION,
    z_score_60          DOUBLE PRECISION,

    -- Macro
    dxy_open            DOUBLE PRECISION,
    dxy_high            DOUBLE PRECISION,
    dxy_low             DOUBLE PRECISION,
    dxy_close           DOUBLE PRECISION,
    fed_funds_rate      DOUBLE PRECISION,
    us_10y_yield        DOUBLE PRECISION,
    cpi                 DOUBLE PRECISION,
    core_cpi            DOUBLE PRECISION,
    breakeven_inflation DOUBLE PRECISION,
    us_2y_yield         DOUBLE PRECISION,
    us_30y_yield        DOUBLE PRECISION,
    yield_curve_slope   DOUBLE PRECISION,
    m2_money_supply     DOUBLE PRECISION,
    unemployment_rate   DOUBLE PRECISION,
    vix                 DOUBLE PRECISION,
    sp500_close         DOUBLE PRECISION,
    silver_close        DOUBLE PRECISION,
    wti_oil_price       DOUBLE PRECISION,
    brent_oil_price     DOUBLE PRECISION,

    -- Ratios
    gold_silver_ratio   DOUBLE PRECISION,
    gold_oil_ratio      DOUBLE PRECISION,
    gold_sp500_ratio    DOUBLE PRECISION,
    gold_dxy_ratio      DOUBLE PRECISION,
    real_yield          DOUBLE PRECISION,
    oil_spread          DOUBLE PRECISION,

    -- Interpretable external market drivers
    gold_gap_pct                      DOUBLE PRECISION,
    gold_intraday_return_pct          DOUBLE PRECISION,
    gold_range_pct                    DOUBLE PRECISION,
    gold_close_location               DOUBLE PRECISION,
    dxy_return_5d                     DOUBLE PRECISION,
    us_10y_real_yield                DOUBLE PRECISION,
    real_yield_change_5d              DOUBLE PRECISION,
    vix_change_5d                     DOUBLE PRECISION,
    sp500_return_5d                   DOUBLE PRECISION,
    gld_return_5d                     DOUBLE PRECISION,
    gld_volume_zscore_21d             DOUBLE PRECISION,
    tlt_return_5d                     DOUBLE PRECISION,
    uup_return_5d                     DOUBLE PRECISION,
    tip_return_5d                     DOUBLE PRECISION,
    hyg_return_5d                     DOUBLE PRECISION,
    economic_policy_uncertainty       DOUBLE PRECISION,
    epu_zscore_63d                    DOUBLE PRECISION,
    high_yield_spread                 DOUBLE PRECISION,
    high_yield_spread_change_5d       DOUBLE PRECISION,
    cftc_mm_net_pct_oi                DOUBLE PRECISION,
    cftc_mm_net_change_pct_oi         DOUBLE PRECISION,
    cftc_producer_net_pct_oi          DOUBLE PRECISION,
    cftc_swap_net_pct_oi              DOUBLE PRECISION,
    cftc_mm_net_zscore_52w            DOUBLE PRECISION,
    cftc_positioning_age_days         INTEGER,

    -- Sliding Windows
    gold_avg_5d         DOUBLE PRECISION,
    gold_pct_chg_5d     DOUBLE PRECISION,
    gold_avg_21d        DOUBLE PRECISION,
    gold_pct_chg_21d    DOUBLE PRECISION,
    gold_avg_63d        DOUBLE PRECISION,
    gold_pct_chg_63d    DOUBLE PRECISION,
    gold_avg_252d       DOUBLE PRECISION,
    gold_pct_chg_252d   DOUBLE PRECISION,

    -- Calendar and historical analog features
    month_num                       INTEGER,
    quarter_num                     INTEGER,
    iso_week_num                    INTEGER,
    day_of_year                     INTEGER,
    month_sin                       DOUBLE PRECISION,
    month_cos                       DOUBLE PRECISION,
    year_sin                        DOUBLE PRECISION,
    year_cos                        DOUBLE PRECISION,
    month_progress                  DOUBLE PRECISION,
    quarter_progress                DOUBLE PRECISION,
    year_progress                   DOUBLE PRECISION,
    days_to_year_end                INTEGER,
    month_to_date_return            DOUBLE PRECISION,
    quarter_to_date_return          DOUBLE PRECISION,
    year_to_date_return             DOUBLE PRECISION,
    same_month_return_5d_mean       DOUBLE PRECISION,
    same_month_return_5d_std        DOUBLE PRECISION,
    same_month_up_rate_5d           DOUBLE PRECISION,
    same_month_samples_5d           INTEGER,
    same_month_return_7d_mean       DOUBLE PRECISION,
    same_month_up_rate_7d           DOUBLE PRECISION,
    same_month_samples_7d           INTEGER,
    same_month_return_21d_mean      DOUBLE PRECISION,
    same_month_up_rate_21d          DOUBLE PRECISION,
    same_month_samples_21d          INTEGER,
    same_quarter_return_21d_mean    DOUBLE PRECISION,
    same_quarter_up_rate_21d        DOUBLE PRECISION,
    same_quarter_samples_21d        INTEGER,
    same_doy_return_5d_mean         DOUBLE PRECISION,
    same_doy_return_5d_std          DOUBLE PRECISION,
    same_doy_up_rate_5d             DOUBLE PRECISION,
    same_doy_samples_5d             INTEGER,
    same_doy_return_7d_mean         DOUBLE PRECISION,
    same_doy_up_rate_7d             DOUBLE PRECISION,
    same_doy_samples_7d             INTEGER,
    same_doy_return_10d_mean        DOUBLE PRECISION,
    same_doy_up_rate_10d            DOUBLE PRECISION,
    same_doy_return_21d_mean        DOUBLE PRECISION,
    same_doy_up_rate_21d            DOUBLE PRECISION,
    same_doy_samples_21d            INTEGER,
    regime_return_5d_mean           DOUBLE PRECISION,
    regime_up_rate_5d               DOUBLE PRECISION,
    regime_samples_5d               INTEGER,
    regime_return_7d_mean           DOUBLE PRECISION,
    regime_up_rate_7d               DOUBLE PRECISION,
    regime_samples_7d               INTEGER,
    regime_return_10d_mean          DOUBLE PRECISION,
    regime_up_rate_10d              DOUBLE PRECISION,
    regime_return_21d_mean          DOUBLE PRECISION,
    regime_up_rate_21d              DOUBLE PRECISION,
    regime_samples_21d              INTEGER,

    -- EWMA Features (7d / 30d / 90d / 365d calendar)
    ewma_7d             DOUBLE PRECISION,
    ewma_30d            DOUBLE PRECISION,
    ewma_90d            DOUBLE PRECISION,
    ewma_365d           DOUBLE PRECISION,
    ewma_vol_7d         DOUBLE PRECISION,
    ewma_vol_30d        DOUBLE PRECISION,
    ewma_vol_90d        DOUBLE PRECISION,
    ewma_vol_365d       DOUBLE PRECISION,
    price_vs_ewma_7d    DOUBLE PRECISION,
    price_vs_ewma_30d   DOUBLE PRECISION,
    price_vs_ewma_90d   DOUBLE PRECISION,
    price_vs_ewma_365d  DOUBLE PRECISION,
    ewma_cross_7_30     DOUBLE PRECISION,
    ewma_cross_30_90    DOUBLE PRECISION,
    ewma_cross_90_365   DOUBLE PRECISION,

    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE features.master_features
    ADD COLUMN IF NOT EXISTS gold_close DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS gold_open DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS gold_gap_pct DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS gold_intraday_return_pct DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS gold_range_pct DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS gold_close_location DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS dxy_return_5d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS us_10y_real_yield DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS real_yield_change_5d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS vix_change_5d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS sp500_return_5d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS gld_return_5d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS gld_volume_zscore_21d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS tlt_return_5d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS uup_return_5d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS tip_return_5d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS hyg_return_5d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS economic_policy_uncertainty DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS epu_zscore_63d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS high_yield_spread DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS high_yield_spread_change_5d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS cftc_mm_net_pct_oi DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS cftc_mm_net_change_pct_oi DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS cftc_producer_net_pct_oi DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS cftc_swap_net_pct_oi DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS cftc_mm_net_zscore_52w DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS cftc_positioning_age_days INTEGER,
    ADD COLUMN IF NOT EXISTS month_num INTEGER,
    ADD COLUMN IF NOT EXISTS quarter_num INTEGER,
    ADD COLUMN IF NOT EXISTS iso_week_num INTEGER,
    ADD COLUMN IF NOT EXISTS day_of_year INTEGER,
    ADD COLUMN IF NOT EXISTS month_sin DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS month_cos DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS year_sin DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS year_cos DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS month_progress DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS quarter_progress DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS year_progress DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS days_to_year_end INTEGER,
    ADD COLUMN IF NOT EXISTS month_to_date_return DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS quarter_to_date_return DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS year_to_date_return DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS same_month_return_5d_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS same_month_return_5d_std DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS same_month_up_rate_5d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS same_month_samples_5d INTEGER,
    ADD COLUMN IF NOT EXISTS same_month_return_7d_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS same_month_up_rate_7d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS same_month_samples_7d INTEGER,
    ADD COLUMN IF NOT EXISTS same_month_return_21d_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS same_month_up_rate_21d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS same_month_samples_21d INTEGER,
    ADD COLUMN IF NOT EXISTS same_quarter_return_21d_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS same_quarter_up_rate_21d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS same_quarter_samples_21d INTEGER,
    ADD COLUMN IF NOT EXISTS same_doy_return_5d_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS same_doy_return_5d_std DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS same_doy_up_rate_5d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS same_doy_samples_5d INTEGER,
    ADD COLUMN IF NOT EXISTS same_doy_return_7d_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS same_doy_up_rate_7d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS same_doy_samples_7d INTEGER,
    ADD COLUMN IF NOT EXISTS same_doy_return_10d_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS same_doy_up_rate_10d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS same_doy_return_21d_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS same_doy_up_rate_21d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS same_doy_samples_21d INTEGER,
    ADD COLUMN IF NOT EXISTS regime_return_5d_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS regime_up_rate_5d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS regime_samples_5d INTEGER,
    ADD COLUMN IF NOT EXISTS regime_return_7d_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS regime_up_rate_7d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS regime_samples_7d INTEGER,
    ADD COLUMN IF NOT EXISTS regime_return_10d_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS regime_up_rate_10d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS regime_return_21d_mean DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS regime_up_rate_21d DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS regime_samples_21d INTEGER;

ALTER TABLE features.target_labels
    ADD COLUMN IF NOT EXISTS next_1_day_open DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS next_2_day_open DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS next_3_day_open DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS next_4_day_open DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS next_5_day_open DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS next_6_day_open DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS next_7_day_open DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS next_8_day_open DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS next_9_day_open DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS next_10_day_open DOUBLE PRECISION;

ALTER TABLE features.target_labels
    DROP COLUMN IF EXISTS next_1_day_price,
    DROP COLUMN IF EXISTS next_3_day_price,
    DROP COLUMN IF EXISTS next_5_day_price,
    DROP COLUMN IF EXISTS next_7_day_price,
    DROP COLUMN IF EXISTS next_10_day_price,
    DROP COLUMN IF EXISTS next_21_day_price,
    DROP COLUMN IF EXISTS next_30_day_price,
    DROP COLUMN IF EXISTS next_63_day_price,
    DROP COLUMN IF EXISTS next_1_day_direction,
    DROP COLUMN IF EXISTS next_3_day_direction,
    DROP COLUMN IF EXISTS next_5_day_direction,
    DROP COLUMN IF EXISTS next_7_day_direction,
    DROP COLUMN IF EXISTS next_10_day_direction,
    DROP COLUMN IF EXISTS next_21_day_direction,
    DROP COLUMN IF EXISTS next_30_day_direction,
    DROP COLUMN IF EXISTS next_63_day_direction,
    DROP COLUMN IF EXISTS next_1_day_price_change,
    DROP COLUMN IF EXISTS next_3_day_price_change,
    DROP COLUMN IF EXISTS next_5_day_price_change,
    DROP COLUMN IF EXISTS next_7_day_price_change,
    DROP COLUMN IF EXISTS next_10_day_price_change,
    DROP COLUMN IF EXISTS next_21_day_price_change,
    DROP COLUMN IF EXISTS next_30_day_price_change,
    DROP COLUMN IF EXISTS next_63_day_price_change;

ALTER TABLE features.macro_features
    DROP COLUMN IF EXISTS us_interest_rate,
    DROP COLUMN IF EXISTS us_inflation_yoy;

ALTER TABLE features.master_features
    DROP COLUMN IF EXISTS us_interest_rate,
    DROP COLUMN IF EXISTS us_inflation_yoy;

CREATE INDEX IF NOT EXISTS idx_master_features_date ON features.master_features (date);
