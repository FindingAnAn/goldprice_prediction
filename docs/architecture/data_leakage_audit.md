# Data Leakage Audit

## Kết luận

Không phát hiện target leakage trực tiếp trong production training path hiện
tại. Các boundary chính đã được bảo vệ bằng SQL, feature filter và chronological
evaluation. Vẫn còn residual point-in-time risk từ revision/release timestamp
của FRED; vì vậy kết quả là research-grade, chưa phải trading-grade.

## Audit theo lớp

| Risk | Control | Trạng thái |
|---|---|---|
| Future target trong feature | Target ở bảng riêng; prefix `next_<n>_day_` bị chặn | Đã kiểm soát |
| Random split | Chronological split và rolling windows | Đã kiểm soát |
| Future observations trong train | Mỗi rolling cutoff chỉ train trên quá khứ | Đã kiểm soát |
| CFTC Tuesday report dùng trước Friday | Join từ `available_date = report_date + 3` | Đã kiểm soát |
| Seasonal analog dùng tương lai gần | Chỉ dùng historical row ít nhất 1 năm trước | Đã kiểm soát |
| Monthly macro revision | Cấm các cột monthly trong model | Đã kiểm soát |
| Daily FRED vintage/release | Observation date + 1 ngày, không có ALFRED vintage | Rủi ro còn lại |
| Current OHLCV | Chỉ hợp lệ vì cutoff là sau phiên | Điều kiện bắt buộc |

## Target isolation

`features.master_features` không join `features.target_labels`. Sequence model
dùng chuỗi `gold_open`; direct model tạo target theo từng horizon trong memory.
Bảng target label chỉ phục vụ EDA/kiểm tra. Các utility EDA loại:

- toàn bộ `OPEN_TARGET_COLUMNS`;
- mọi cột khớp `^next_\d+_day_`;
- danh sách `POINT_IN_TIME_UNSAFE_FEATURE_COLUMNS`.

## Validation protocol

- Deep models: rolling cross-validation, step size 10, không shuffle.
- Direct model horizon `h`: train kết thúc tại `cutoff - h`; target là
  `log(open[t+h]/close[t])`.
- Direct models dùng rolling training window 1.260 phiên; không backward-fill.
- Model selection: rolling RMSE; final future data không tham gia selection.
- Production refit chỉ chạy sau evaluation.

## Seasonal analog

Feature analog có thể dùng `LEAD()` để tính outcome của một historical row,
nhưng row đó phải cách current row ít nhất một năm. Do horizon lớn nhất 21 phiên,
outcome đã được biết nhiều tháng trước current date.

## Việc cần làm nếu đưa vào trading

1. Thay FRED bằng ALFRED vintage hoặc release-calendar point-in-time dataset.
2. Dùng CME trading calendar chính thức.
3. Version raw snapshot thay vì truncate.
4. Thêm walk-forward benchmark theo regime và transaction-aware decision rule.
