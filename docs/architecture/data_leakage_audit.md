# Data Leakage Audit

## Kết luận

Pipeline modeling chính hiện chặn hai nhóm leakage:

1. Tất cả target tương lai `next_*_day_*`.
2. FRED monthly chưa point-in-time safe:
   `fed_funds_rate`, `us_interest_rate`, `us_inflation_yoy`, `cpi`,
   `core_cpi`, `m2_money_supply`, `unemployment_rate`.

Nhóm FRED monthly vẫn được giữ trong database phục vụ EDA, nhưng không được
đưa vào training hoặc AutoGluon benchmark.

Forward-fill daily chỉ được phép nhìn về quá khứ tối đa `max_gap_days`; không
backfill và không kéo giá trị cũ vô hạn.

## Leakage đã phát hiện

`sql/schema/00_populate_staging.sql` gán observation monthly cho toàn bộ ngày
trong cùng tháng. Trong thực tế, CPI, unemployment, M2 và các chỉ số tương tự
được công bố sau observation period. API FRED hiện tại cũng trả về series có
thể đã được revision. Vì vậy historical backtest có thể nhìn thấy thông tin
chưa tồn tại tại thời điểm dự báo.

## Các phần hiện an toàn

- Target `next_7_day_price` nằm riêng trong `features.target_labels`.
- Training frame chỉ join đúng một target được chọn.
- Feature inference và validation chặn mọi cột `next_*_day_*`.
- Train/test và `TimeSeriesSplit` có purge gap bằng forecast horizon.
- AutoGluon dùng validation theo thời gian và final holdout riêng.
- Rolling SQL dùng `PRECEDING ... CURRENT ROW`, không dùng `FOLLOWING`.
- Notebook modeling không dùng test set cho early stopping/Optuna; Optuna chỉ
  dùng `TimeSeriesSplit(gap=7)` trên train.
- Notebook holdout chỉ dùng để so sánh; model production được chọn bằng CV
  trong `src/modeling/train.py`, không chọn lại theo holdout.

## Giả định thời điểm dự báo

Prediction được tạo sau khi phiên giao dịch ngày `t` đã đóng cửa. Do đó các
feature dùng close/high/low ngày `t` là hợp lệ. Nếu dự báo trước hoặc trong
phiên, các feature này phải được lag ít nhất một phiên.

## Cách mở lại FRED monthly

Chỉ đưa các cột trên trở lại model khi ingestion lưu được:

- release timestamp thực tế;
- vintage/realtime date tại thời điểm lịch sử;
- as-of join: `release_timestamp <= prediction_timestamp`.

ALFRED/FRED vintage data hoặc một economic-calendar source có release timestamp
là phương án phù hợp.
