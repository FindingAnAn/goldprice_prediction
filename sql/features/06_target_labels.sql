-- Future gold-open targets for the next 10 trading sessions.
-- Targets remain isolated from features.master_features.

WITH future_opens AS (
    SELECT
        date,
        LEAD(gold_open, 1)  OVER (ORDER BY date) AS open_1d,
        LEAD(gold_open, 2)  OVER (ORDER BY date) AS open_2d,
        LEAD(gold_open, 3)  OVER (ORDER BY date) AS open_3d,
        LEAD(gold_open, 4)  OVER (ORDER BY date) AS open_4d,
        LEAD(gold_open, 5)  OVER (ORDER BY date) AS open_5d,
        LEAD(gold_open, 6)  OVER (ORDER BY date) AS open_6d,
        LEAD(gold_open, 7)  OVER (ORDER BY date) AS open_7d,
        LEAD(gold_open, 8)  OVER (ORDER BY date) AS open_8d,
        LEAD(gold_open, 9)  OVER (ORDER BY date) AS open_9d,
        LEAD(gold_open, 10) OVER (ORDER BY date) AS open_10d
    FROM staging.daily_master
    WHERE gold_close IS NOT NULL
      AND gold_open IS NOT NULL
      AND date >= '2010-01-01'
)
INSERT INTO features.target_labels (
    date,
    next_1_day_open,
    next_2_day_open,
    next_3_day_open,
    next_4_day_open,
    next_5_day_open,
    next_6_day_open,
    next_7_day_open,
    next_8_day_open,
    next_9_day_open,
    next_10_day_open,
    updated_at
)
SELECT
    date,
    open_1d,
    open_2d,
    open_3d,
    open_4d,
    open_5d,
    open_6d,
    open_7d,
    open_8d,
    open_9d,
    open_10d,
    NOW()
FROM future_opens
ON CONFLICT (date) DO UPDATE SET
    next_1_day_open = EXCLUDED.next_1_day_open,
    next_2_day_open = EXCLUDED.next_2_day_open,
    next_3_day_open = EXCLUDED.next_3_day_open,
    next_4_day_open = EXCLUDED.next_4_day_open,
    next_5_day_open = EXCLUDED.next_5_day_open,
    next_6_day_open = EXCLUDED.next_6_day_open,
    next_7_day_open = EXCLUDED.next_7_day_open,
    next_8_day_open = EXCLUDED.next_8_day_open,
    next_9_day_open = EXCLUDED.next_9_day_open,
    next_10_day_open = EXCLUDED.next_10_day_open,
    updated_at = NOW();
