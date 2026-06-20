-- Price indicators using past and current observations only.

WITH ordered AS (
    SELECT
        date,
        gold_close,
        ROW_NUMBER() OVER (ORDER BY date) AS rn
    FROM staging.daily_master
    WHERE gold_close IS NOT NULL
      AND date >= '2010-01-01'
),
sma_calc AS (
    SELECT
        date,
        gold_close,
        rn,
        AVG(gold_close) OVER (ORDER BY date ROWS BETWEEN 9 PRECEDING AND CURRENT ROW) AS sma_10,
        AVG(gold_close) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS sma_20,
        AVG(gold_close) OVER (ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS sma_50,
        AVG(gold_close) OVER (ORDER BY date ROWS BETWEEN 99 PRECEDING AND CURRENT ROW) AS sma_100,
        AVG(gold_close) OVER (ORDER BY date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) AS sma_200,
        STDDEV(gold_close) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS std_20
    FROM ordered
),
ema_calc AS (
    SELECT
        current_row.date,
        SUM(
            history.gold_close
            * POWER(1.0 - 2.0 / 11.0, current_row.rn - history.rn)
        ) FILTER (WHERE history.rn >= current_row.rn - 9)
        / NULLIF(
            SUM(
                POWER(1.0 - 2.0 / 11.0, current_row.rn - history.rn)
            ) FILTER (WHERE history.rn >= current_row.rn - 9),
            0
        ) AS ema_10,
        SUM(
            history.gold_close
            * POWER(1.0 - 2.0 / 21.0, current_row.rn - history.rn)
        ) FILTER (WHERE history.rn >= current_row.rn - 19)
        / NULLIF(
            SUM(
                POWER(1.0 - 2.0 / 21.0, current_row.rn - history.rn)
            ) FILTER (WHERE history.rn >= current_row.rn - 19),
            0
        ) AS ema_20,
        SUM(
            history.gold_close
            * POWER(1.0 - 2.0 / 51.0, current_row.rn - history.rn)
        ) FILTER (WHERE history.rn >= current_row.rn - 49)
        / NULLIF(
            SUM(
                POWER(1.0 - 2.0 / 51.0, current_row.rn - history.rn)
            ) FILTER (WHERE history.rn >= current_row.rn - 49),
            0
        ) AS ema_50,
        SUM(
            history.gold_close
            * POWER(1.0 - 2.0 / 101.0, current_row.rn - history.rn)
        ) FILTER (WHERE history.rn >= current_row.rn - 99)
        / NULLIF(
            SUM(
                POWER(1.0 - 2.0 / 101.0, current_row.rn - history.rn)
            ) FILTER (WHERE history.rn >= current_row.rn - 99),
            0
        ) AS ema_100,
        SUM(
            history.gold_close
            * POWER(1.0 - 2.0 / 201.0, current_row.rn - history.rn)
        )
        / NULLIF(
            SUM(POWER(1.0 - 2.0 / 201.0, current_row.rn - history.rn)),
            0
        ) AS ema_200
    FROM ordered current_row
    JOIN ordered history
      ON history.rn BETWEEN GREATEST(1, current_row.rn - 199) AND current_row.rn
    GROUP BY current_row.date, current_row.rn
)
INSERT INTO features.price_indicators (
    date, gold_close,
    sma_10, sma_20, sma_50, sma_100, sma_200,
    ema_10, ema_20, ema_50, ema_100, ema_200,
    bb_upper, bb_lower, bb_width, bb_pct,
    updated_at
)
SELECT
    sma.date,
    sma.gold_close,
    sma.sma_10,
    sma.sma_20,
    sma.sma_50,
    sma.sma_100,
    sma.sma_200,
    ema.ema_10,
    ema.ema_20,
    ema.ema_50,
    ema.ema_100,
    ema.ema_200,
    sma.sma_20 + 2 * sma.std_20 AS bb_upper,
    sma.sma_20 - 2 * sma.std_20 AS bb_lower,
    CASE
        WHEN sma.sma_20 > 0 THEN 4 * sma.std_20 / sma.sma_20
    END AS bb_width,
    CASE
        WHEN 4 * sma.std_20 > 0
        THEN (
            sma.gold_close - (sma.sma_20 - 2 * sma.std_20)
        ) / (4 * sma.std_20)
    END AS bb_pct,
    NOW()
FROM sma_calc sma
JOIN ema_calc ema ON sma.date = ema.date
ON CONFLICT (date) DO UPDATE SET
    gold_close = EXCLUDED.gold_close,
    sma_10 = EXCLUDED.sma_10,
    sma_20 = EXCLUDED.sma_20,
    sma_50 = EXCLUDED.sma_50,
    sma_100 = EXCLUDED.sma_100,
    sma_200 = EXCLUDED.sma_200,
    ema_10 = EXCLUDED.ema_10,
    ema_20 = EXCLUDED.ema_20,
    ema_50 = EXCLUDED.ema_50,
    ema_100 = EXCLUDED.ema_100,
    ema_200 = EXCLUDED.ema_200,
    bb_upper = EXCLUDED.bb_upper,
    bb_lower = EXCLUDED.bb_lower,
    bb_width = EXCLUDED.bb_width,
    bb_pct = EXCLUDED.bb_pct,
    updated_at = NOW();
