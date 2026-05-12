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
-- DXY OHLC, Fed Funds, yields, inflation, usintr, usiryy
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
    us_interest_rate    DOUBLE PRECISION,   -- USINTR → usintr
    us_10y_yield        DOUBLE PRECISION,   -- DGS10

    -- Inflation
    us_inflation_yoy    DOUBLE PRECISION,   -- FPCPITOTLZGUSA → usiryy
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
-- features.target_labels  (TÁCH RIÊNG — không join vào master_features)
-- Chứa target variables: next N-day price/direction/change
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS features.target_labels (
    date                    DATE             NOT NULL PRIMARY KEY,

    -- Next N-day price (LEAD)
    next_1_day_price        DOUBLE PRECISION,
    next_3_day_price        DOUBLE PRECISION,
    next_7_day_price        DOUBLE PRECISION,
    next_30_day_price       DOUBLE PRECISION,

    -- Direction: 1 = up, 0 = down/flat
    next_1_day_direction    SMALLINT,
    next_3_day_direction    SMALLINT,
    next_7_day_direction    SMALLINT,
    next_30_day_direction   SMALLINT,

    -- Price change %
    next_1_day_price_change  DOUBLE PRECISION,
    next_3_day_price_change  DOUBLE PRECISION,
    next_7_day_price_change  DOUBLE PRECISION,
    next_30_day_price_change DOUBLE PRECISION,

    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- features.master_features
-- JOIN tất cả features — KHÔNG chứa target labels (anti-leakage)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS features.master_features (
    date                DATE             NOT NULL PRIMARY KEY,

    -- From staging.daily_master (raw values)
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
    us_interest_rate    DOUBLE PRECISION,
    us_10y_yield        DOUBLE PRECISION,
    us_inflation_yoy    DOUBLE PRECISION,
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

    -- Sliding Windows
    gold_avg_5d         DOUBLE PRECISION,
    gold_pct_chg_5d     DOUBLE PRECISION,
    gold_avg_21d        DOUBLE PRECISION,
    gold_pct_chg_21d    DOUBLE PRECISION,
    gold_avg_63d        DOUBLE PRECISION,
    gold_pct_chg_63d    DOUBLE PRECISION,
    gold_avg_252d       DOUBLE PRECISION,
    gold_pct_chg_252d   DOUBLE PRECISION,

    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_master_features_date ON features.master_features (date);
