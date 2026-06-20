-- Finite exponentially weighted features using past and current rows only.

WITH base AS (
    SELECT
        date,
        gold_close,
        gold_volume,
        ROW_NUMBER() OVER (ORDER BY date) AS rn
    FROM staging.daily_master
    WHERE gold_close IS NOT NULL
      AND date >= '2010-01-01'
),
weighted AS (
    SELECT
        current_row.date,
        SUM(
            history.gold_close
            * POWER(1.0 - 2.0 / 6.0, current_row.rn - history.rn)
        ) FILTER (WHERE history.rn >= current_row.rn - 4)
        / NULLIF(
            SUM(
                POWER(1.0 - 2.0 / 6.0, current_row.rn - history.rn)
            ) FILTER (WHERE history.rn >= current_row.rn - 4),
            0
        ) AS ewma_7d,
        SUM(
            history.gold_close
            * POWER(1.0 - 2.0 / 22.0, current_row.rn - history.rn)
        ) FILTER (WHERE history.rn >= current_row.rn - 20)
        / NULLIF(
            SUM(
                POWER(1.0 - 2.0 / 22.0, current_row.rn - history.rn)
            ) FILTER (WHERE history.rn >= current_row.rn - 20),
            0
        ) AS ewma_30d,
        SUM(
            history.gold_close
            * POWER(1.0 - 2.0 / 64.0, current_row.rn - history.rn)
        ) FILTER (WHERE history.rn >= current_row.rn - 62)
        / NULLIF(
            SUM(
                POWER(1.0 - 2.0 / 64.0, current_row.rn - history.rn)
            ) FILTER (WHERE history.rn >= current_row.rn - 62),
            0
        ) AS ewma_90d,
        SUM(
            history.gold_close
            * POWER(1.0 - 2.0 / 253.0, current_row.rn - history.rn)
        )
        / NULLIF(
            SUM(POWER(1.0 - 2.0 / 253.0, current_row.rn - history.rn)),
            0
        ) AS ewma_365d,
        SUM(
            history.gold_volume
            * POWER(1.0 - 2.0 / 6.0, current_row.rn - history.rn)
        ) FILTER (
            WHERE history.rn >= current_row.rn - 4
              AND history.gold_volume IS NOT NULL
        )
        / NULLIF(
            SUM(
                POWER(1.0 - 2.0 / 6.0, current_row.rn - history.rn)
            ) FILTER (
                WHERE history.rn >= current_row.rn - 4
                  AND history.gold_volume IS NOT NULL
            ),
            0
        ) AS ewma_vol_7d,
        SUM(
            history.gold_volume
            * POWER(1.0 - 2.0 / 22.0, current_row.rn - history.rn)
        ) FILTER (
            WHERE history.rn >= current_row.rn - 20
              AND history.gold_volume IS NOT NULL
        )
        / NULLIF(
            SUM(
                POWER(1.0 - 2.0 / 22.0, current_row.rn - history.rn)
            ) FILTER (
                WHERE history.rn >= current_row.rn - 20
                  AND history.gold_volume IS NOT NULL
            ),
            0
        ) AS ewma_vol_30d,
        SUM(
            history.gold_volume
            * POWER(1.0 - 2.0 / 64.0, current_row.rn - history.rn)
        ) FILTER (
            WHERE history.rn >= current_row.rn - 62
              AND history.gold_volume IS NOT NULL
        )
        / NULLIF(
            SUM(
                POWER(1.0 - 2.0 / 64.0, current_row.rn - history.rn)
            ) FILTER (
                WHERE history.rn >= current_row.rn - 62
                  AND history.gold_volume IS NOT NULL
            ),
            0
        ) AS ewma_vol_90d,
        SUM(
            history.gold_volume
            * POWER(1.0 - 2.0 / 253.0, current_row.rn - history.rn)
        ) FILTER (WHERE history.gold_volume IS NOT NULL)
        / NULLIF(
            SUM(
                POWER(1.0 - 2.0 / 253.0, current_row.rn - history.rn)
            ) FILTER (WHERE history.gold_volume IS NOT NULL),
            0
        ) AS ewma_vol_365d
    FROM base current_row
    JOIN base history
      ON history.rn BETWEEN GREATEST(1, current_row.rn - 251) AND current_row.rn
    GROUP BY current_row.date, current_row.rn
)
INSERT INTO features.ewma_features (
    date,
    ewma_7d, ewma_30d, ewma_90d, ewma_365d,
    ewma_vol_7d, ewma_vol_30d, ewma_vol_90d, ewma_vol_365d,
    price_vs_ewma_7d, price_vs_ewma_30d,
    price_vs_ewma_90d, price_vs_ewma_365d,
    ewma_cross_7_30, ewma_cross_30_90, ewma_cross_90_365,
    updated_at
)
SELECT
    base.date,
    weighted.ewma_7d,
    weighted.ewma_30d,
    weighted.ewma_90d,
    weighted.ewma_365d,
    weighted.ewma_vol_7d,
    weighted.ewma_vol_30d,
    weighted.ewma_vol_90d,
    weighted.ewma_vol_365d,
    CASE WHEN weighted.ewma_7d > 0
        THEN (base.gold_close - weighted.ewma_7d) / weighted.ewma_7d * 100.0
    END,
    CASE WHEN weighted.ewma_30d > 0
        THEN (base.gold_close - weighted.ewma_30d) / weighted.ewma_30d * 100.0
    END,
    CASE WHEN weighted.ewma_90d > 0
        THEN (base.gold_close - weighted.ewma_90d) / weighted.ewma_90d * 100.0
    END,
    CASE WHEN weighted.ewma_365d > 0
        THEN (base.gold_close - weighted.ewma_365d) / weighted.ewma_365d * 100.0
    END,
    CASE WHEN weighted.ewma_7d > weighted.ewma_30d THEN 1.0 ELSE -1.0 END,
    CASE WHEN weighted.ewma_30d > weighted.ewma_90d THEN 1.0 ELSE -1.0 END,
    CASE WHEN weighted.ewma_90d > weighted.ewma_365d THEN 1.0 ELSE -1.0 END,
    NOW()
FROM base
JOIN weighted ON base.date = weighted.date
ON CONFLICT (date) DO UPDATE SET
    ewma_7d = EXCLUDED.ewma_7d,
    ewma_30d = EXCLUDED.ewma_30d,
    ewma_90d = EXCLUDED.ewma_90d,
    ewma_365d = EXCLUDED.ewma_365d,
    ewma_vol_7d = EXCLUDED.ewma_vol_7d,
    ewma_vol_30d = EXCLUDED.ewma_vol_30d,
    ewma_vol_90d = EXCLUDED.ewma_vol_90d,
    ewma_vol_365d = EXCLUDED.ewma_vol_365d,
    price_vs_ewma_7d = EXCLUDED.price_vs_ewma_7d,
    price_vs_ewma_30d = EXCLUDED.price_vs_ewma_30d,
    price_vs_ewma_90d = EXCLUDED.price_vs_ewma_90d,
    price_vs_ewma_365d = EXCLUDED.price_vs_ewma_365d,
    ewma_cross_7_30 = EXCLUDED.ewma_cross_7_30,
    ewma_cross_30_90 = EXCLUDED.ewma_cross_30_90,
    ewma_cross_90_365 = EXCLUDED.ewma_cross_90_365,
    updated_at = NOW();
