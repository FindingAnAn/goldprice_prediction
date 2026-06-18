-- =============================================================================
-- sql/schema/00_populate_staging.sql
-- Populate staging.daily_master từ raw tables.
-- Chạy sau khi ingest xong raw data và trước khi tính feature.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Bước 1: Upsert gold_close từ raw.gold_prices
-- Ưu tiên yfinance_gcf (mới nhất), fallback freegoldapi
-- ---------------------------------------------------------------------------
INSERT INTO staging.daily_master (date, gold_close, gold_open, gold_high, gold_low, gold_volume)
SELECT
    COALESCE(yf.date, fg.date)          AS date,
    COALESCE(yf.close, fg.price)        AS gold_close,
    yf.open                             AS gold_open,
    yf.high                             AS gold_high,
    yf.low                              AS gold_low,
    yf.volume                           AS gold_volume
FROM
    (SELECT date, open, high, low, close, volume
     FROM raw.yfinance_daily WHERE ticker = 'GC=F') yf
FULL OUTER JOIN
    (SELECT date, price FROM raw.gold_prices WHERE source = 'freegoldapi') fg
    ON yf.date = fg.date
ON CONFLICT (date) DO UPDATE SET
    gold_close  = EXCLUDED.gold_close,
    gold_open   = EXCLUDED.gold_open,
    gold_high   = EXCLUDED.gold_high,
    gold_low    = EXCLUDED.gold_low,
    gold_volume = EXCLUDED.gold_volume,
    updated_at  = NOW();

-- ---------------------------------------------------------------------------
-- Bước 2: Upsert DXY (DX-Y.NYB OHLC)
-- ---------------------------------------------------------------------------
INSERT INTO staging.daily_master (date, dxy_open, dxy_high, dxy_low, dxy_close)
SELECT date, open AS dxy_open, high AS dxy_high, low AS dxy_low, close AS dxy_close
FROM raw.yfinance_daily
WHERE ticker = 'DX-Y.NYB'
ON CONFLICT (date) DO UPDATE SET
    dxy_open  = EXCLUDED.dxy_open,
    dxy_high  = EXCLUDED.dxy_high,
    dxy_low   = EXCLUDED.dxy_low,
    dxy_close = EXCLUDED.dxy_close,
    updated_at = NOW();

-- ---------------------------------------------------------------------------
-- Bước 3: Upsert Silver (SI=F)
-- ---------------------------------------------------------------------------
INSERT INTO staging.daily_master (date, silver_open, silver_high, silver_low, silver_close)
SELECT date, open AS silver_open, high AS silver_high, low AS silver_low, close AS silver_close
FROM raw.yfinance_daily
WHERE ticker = 'SI=F'
ON CONFLICT (date) DO UPDATE SET
    silver_open  = EXCLUDED.silver_open,
    silver_high  = EXCLUDED.silver_high,
    silver_low   = EXCLUDED.silver_low,
    silver_close = EXCLUDED.silver_close,
    updated_at   = NOW();

-- ---------------------------------------------------------------------------
-- Bước 4: Upsert S&P 500 và VIX
-- ---------------------------------------------------------------------------
INSERT INTO staging.daily_master (date, sp500_close)
SELECT date, close AS sp500_close
FROM raw.yfinance_daily WHERE ticker = '^GSPC'
ON CONFLICT (date) DO UPDATE SET
    sp500_close = EXCLUDED.sp500_close, updated_at = NOW();

INSERT INTO staging.daily_master (date, vix)
SELECT date, close AS vix
FROM raw.yfinance_daily WHERE ticker = '^VIX'
ON CONFLICT (date) DO UPDATE SET
    vix = EXCLUDED.vix, updated_at = NOW();

-- ---------------------------------------------------------------------------
-- Bước 5: Upsert Oil Prices (EIA, fallback yfinance)
-- ---------------------------------------------------------------------------
INSERT INTO staging.daily_master (date, wti_oil_price)
SELECT date, value AS wti_oil_price
FROM raw.eia_oil WHERE series_id = 'RWTC'
ON CONFLICT (date) DO UPDATE SET
    wti_oil_price = EXCLUDED.wti_oil_price, updated_at = NOW();

INSERT INTO staging.daily_master (date, brent_oil_price)
SELECT date, value AS brent_oil_price
FROM raw.eia_oil WHERE series_id = 'RBRTE'
ON CONFLICT (date) DO UPDATE SET
    brent_oil_price = EXCLUDED.brent_oil_price, updated_at = NOW();

-- EIA spot prices thường trễ vài ngày. Bổ sung phần tail bằng oil futures,
-- nhưng không ghi đè ngày đã có dữ liệu EIA.
INSERT INTO staging.daily_master (date, wti_oil_price)
SELECT yf.date, yf.close
FROM raw.yfinance_daily yf
WHERE yf.ticker = 'CL=F'
  AND NOT EXISTS (
      SELECT 1
      FROM raw.eia_oil eia
      WHERE eia.date = yf.date AND eia.series_id = 'RWTC'
  )
ON CONFLICT (date) DO UPDATE SET
    wti_oil_price = EXCLUDED.wti_oil_price, updated_at = NOW();

INSERT INTO staging.daily_master (date, brent_oil_price)
SELECT yf.date, yf.close
FROM raw.yfinance_daily yf
WHERE yf.ticker = 'BZ=F'
  AND NOT EXISTS (
      SELECT 1
      FROM raw.eia_oil eia
      WHERE eia.date = yf.date AND eia.series_id = 'RBRTE'
  )
ON CONFLICT (date) DO UPDATE SET
    brent_oil_price = EXCLUDED.brent_oil_price, updated_at = NOW();

-- ---------------------------------------------------------------------------
-- Bước 6: Upsert FRED Daily
-- ---------------------------------------------------------------------------
INSERT INTO staging.daily_master (date, us_10y_yield)
SELECT date, value FROM raw.fred_daily WHERE series_id = 'DGS10'
ON CONFLICT (date) DO UPDATE SET us_10y_yield = EXCLUDED.us_10y_yield, updated_at = NOW();

INSERT INTO staging.daily_master (date, us_2y_yield)
SELECT date, value FROM raw.fred_daily WHERE series_id = 'DGS2'
ON CONFLICT (date) DO UPDATE SET us_2y_yield = EXCLUDED.us_2y_yield, updated_at = NOW();

INSERT INTO staging.daily_master (date, us_30y_yield)
SELECT date, value FROM raw.fred_daily WHERE series_id = 'DGS30'
ON CONFLICT (date) DO UPDATE SET us_30y_yield = EXCLUDED.us_30y_yield, updated_at = NOW();

INSERT INTO staging.daily_master (date, breakeven_inflation)
SELECT date, value FROM raw.fred_daily WHERE series_id = 'T10YIE'
ON CONFLICT (date) DO UPDATE SET breakeven_inflation = EXCLUDED.breakeven_inflation, updated_at = NOW();

INSERT INTO staging.daily_master (date, yield_curve_slope)
SELECT date, value FROM raw.fred_daily WHERE series_id = 'T10Y2Y'
ON CONFLICT (date) DO UPDATE SET yield_curve_slope = EXCLUDED.yield_curve_slope, updated_at = NOW();

-- FRED daily có publication lag. Dùng Yahoo yield index cho các ngày FRED
-- chưa có, nhưng giữ FRED làm nguồn ưu tiên khi cùng ngày.
INSERT INTO staging.daily_master (date, us_10y_yield)
SELECT yf.date, yf.close
FROM raw.yfinance_daily yf
WHERE yf.ticker = '^TNX'
  AND NOT EXISTS (
      SELECT 1
      FROM raw.fred_daily fred
      WHERE fred.date = yf.date AND fred.series_id = 'DGS10'
  )
ON CONFLICT (date) DO UPDATE SET
    us_10y_yield = EXCLUDED.us_10y_yield, updated_at = NOW();

INSERT INTO staging.daily_master (date, us_30y_yield)
SELECT yf.date, yf.close
FROM raw.yfinance_daily yf
WHERE yf.ticker = '^TYX'
  AND NOT EXISTS (
      SELECT 1
      FROM raw.fred_daily fred
      WHERE fred.date = yf.date AND fred.series_id = 'DGS30'
  )
ON CONFLICT (date) DO UPDATE SET
    us_30y_yield = EXCLUDED.us_30y_yield, updated_at = NOW();

-- ---------------------------------------------------------------------------
-- Bước 7: Upsert FRED Monthly (forward-fill vào daily)
-- Dùng CROSS JOIN LATERAL để fill giá trị monthly vào các ngày trong tháng đó
-- ---------------------------------------------------------------------------
UPDATE staging.daily_master
SET
    fed_funds_rate   = monthly_pivot.fed_funds_rate,
    cpi              = monthly_pivot.cpi,
    core_cpi         = monthly_pivot.core_cpi,
    unemployment_rate= monthly_pivot.unemployment_rate,
    m2_money_supply  = monthly_pivot.m2_money_supply,
    us_interest_rate = NULL,
    us_inflation_yoy = NULL,
    retail_sales     = monthly_pivot.retail_sales
FROM (
    SELECT
        date,
        MAX(CASE WHEN series_id = 'FEDFUNDS'        THEN value END) AS fed_funds_rate,
        MAX(CASE WHEN series_id = 'CPIAUCSL'        THEN value END) AS cpi,
        MAX(CASE WHEN series_id = 'CPILFESL'        THEN value END) AS core_cpi,
        MAX(CASE WHEN series_id = 'UNRATE'          THEN value END) AS unemployment_rate,
        MAX(CASE WHEN series_id = 'M2SL'            THEN value END) AS m2_money_supply,
        MAX(CASE WHEN series_id = 'RSXFS'           THEN value END) AS retail_sales
    FROM raw.fred_monthly
    GROUP BY date
) monthly_pivot
JOIN LATERAL (
    SELECT generate_series(
        DATE_TRUNC('month', monthly_pivot.date)::DATE,
        (DATE_TRUNC('month', monthly_pivot.date) + INTERVAL '1 month - 1 day')::DATE,
        '1 day'::INTERVAL
    )::DATE AS dm_date
) days ON TRUE
WHERE staging.daily_master.date = days.dm_date
  AND monthly_pivot.date IS NOT NULL;
