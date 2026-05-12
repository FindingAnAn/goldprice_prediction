-- =============================================================================
-- sql/features/06_target_labels.sql
-- Tính target labels: next N-day price, direction, price change %.
-- Lưu vào features.target_labels (TÁCH RIÊNG — KHÔNG JOIN vào master_features).
--
-- ⚠️  WARNING: Các cột này là TARGET, không được dùng làm input features!
--              Rows gần đây nhất sẽ có NULL (không có future price).
-- =============================================================================

INSERT INTO features.target_labels (
    date,
    -- Next N-day price
    next_1_day_price,
    next_3_day_price,
    next_7_day_price,
    next_30_day_price,
    -- Direction (1 = up, 0 = down/flat)
    next_1_day_direction,
    next_3_day_direction,
    next_7_day_direction,
    next_30_day_direction,
    -- Price change %
    next_1_day_price_change,
    next_3_day_price_change,
    next_7_day_price_change,
    next_30_day_price_change,
    updated_at
)
SELECT
    date,
    -- Future prices using LEAD window function
    LEAD(gold_close,  1) OVER (ORDER BY date)  AS next_1_day_price,
    LEAD(gold_close,  3) OVER (ORDER BY date)  AS next_3_day_price,
    LEAD(gold_close,  7) OVER (ORDER BY date)  AS next_7_day_price,
    LEAD(gold_close, 30) OVER (ORDER BY date)  AS next_30_day_price,

    -- Direction: 1 nếu giá tương lai cao hơn giá hiện tại
    CASE
        WHEN LEAD(gold_close,  1) OVER (ORDER BY date) > gold_close THEN 1
        WHEN LEAD(gold_close,  1) OVER (ORDER BY date) IS NOT NULL  THEN 0
        ELSE NULL
    END AS next_1_day_direction,
    CASE
        WHEN LEAD(gold_close,  3) OVER (ORDER BY date) > gold_close THEN 1
        WHEN LEAD(gold_close,  3) OVER (ORDER BY date) IS NOT NULL  THEN 0
        ELSE NULL
    END AS next_3_day_direction,
    CASE
        WHEN LEAD(gold_close,  7) OVER (ORDER BY date) > gold_close THEN 1
        WHEN LEAD(gold_close,  7) OVER (ORDER BY date) IS NOT NULL  THEN 0
        ELSE NULL
    END AS next_7_day_direction,
    CASE
        WHEN LEAD(gold_close, 30) OVER (ORDER BY date) > gold_close THEN 1
        WHEN LEAD(gold_close, 30) OVER (ORDER BY date) IS NOT NULL  THEN 0
        ELSE NULL
    END AS next_30_day_direction,

    -- Price change percentage
    CASE WHEN gold_close > 0 THEN
        (LEAD(gold_close,  1) OVER (ORDER BY date) - gold_close) / gold_close * 100.0
    END AS next_1_day_price_change,
    CASE WHEN gold_close > 0 THEN
        (LEAD(gold_close,  3) OVER (ORDER BY date) - gold_close) / gold_close * 100.0
    END AS next_3_day_price_change,
    CASE WHEN gold_close > 0 THEN
        (LEAD(gold_close,  7) OVER (ORDER BY date) - gold_close) / gold_close * 100.0
    END AS next_7_day_price_change,
    CASE WHEN gold_close > 0 THEN
        (LEAD(gold_close, 30) OVER (ORDER BY date) - gold_close) / gold_close * 100.0
    END AS next_30_day_price_change,

    NOW()
FROM staging.daily_master
WHERE gold_close IS NOT NULL
  AND date >= '2000-01-01'
ON CONFLICT (date) DO UPDATE SET
    next_1_day_price         = EXCLUDED.next_1_day_price,
    next_3_day_price         = EXCLUDED.next_3_day_price,
    next_7_day_price         = EXCLUDED.next_7_day_price,
    next_30_day_price        = EXCLUDED.next_30_day_price,
    next_1_day_direction     = EXCLUDED.next_1_day_direction,
    next_3_day_direction     = EXCLUDED.next_3_day_direction,
    next_7_day_direction     = EXCLUDED.next_7_day_direction,
    next_30_day_direction    = EXCLUDED.next_30_day_direction,
    next_1_day_price_change  = EXCLUDED.next_1_day_price_change,
    next_3_day_price_change  = EXCLUDED.next_3_day_price_change,
    next_7_day_price_change  = EXCLUDED.next_7_day_price_change,
    next_30_day_price_change = EXCLUDED.next_30_day_price_change,
    updated_at               = NOW();
