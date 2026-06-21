# Pipeline Guide

## 1. Mục tiêu

Pipeline tạo 10 giá trị Open tương ứng 10 phiên giao dịch tiếp theo. Một run
hoàn chỉnh phải có dữ liệu mới, benchmark leakage-safe, artifact filesystem và
bản ghi trong PostgreSQL.

## 2. Luồng chuẩn

```text
prepare schema
  -> register forecasting.model_runs(status=running)
  -> truncate raw/staging/features
  -> ingest API từ 2010-01-01
  -> validate nguồn bắt buộc
  -> build staging + clean
  -> build SQL features + targets
  -> load training frame
  -> sequence models + direct tabular models
  -> rolling evaluation và model selection
  -> refit production models
  -> forecast 10 Open
  -> persist file + DB + resource metrics
  -> complete/failed run
```

Schema `forecasting` không bị truncate. Nếu ingest hoặc training lỗi, run được
đánh dấu `failed` và error được lưu.

## 3. Lệnh vận hành

### Kiểm tra trước khi chạy

```powershell
python scripts/check_environment.py
python scripts/check_data_freshness.py
```

### Full refresh dữ liệu

```powershell
python scripts/run_ingestion.py
```

Lệnh này phá hủy và dựng lại dữ liệu trong `raw`, `staging`, `features`. Không
chạy nếu muốn giữ snapshot raw hiện tại.

### Full forecast

```powershell
python scripts/run_open_forecast.py
```

Mặc định:

- `--windows 6`
- `--max-steps 100`
- random seed `42`

Smoke test:

```powershell
python scripts/run_open_forecast.py --windows 2 --max-steps 2
```

### Chỉ rebuild feature

```powershell
python scripts/rebuild_features.py
```

### Chỉ benchmark sequence

```powershell
python scripts/benchmark_deep_models.py
```

### EDA

```powershell
python scripts/run_eda.py --no-plots
python scripts/analyze_dataset.py
python scripts/analyze_similarity.py
```

## 4. Validation gate

Sau full refresh, pipeline dừng nếu thiếu:

- gold primary;
- Yahoo `GC=F`;
- FRED `DFII10`;
- FRED `USEPUINDXD`;
- CFTC gold;
- ít nhất 1.000 dòng trong `staging.daily_master`;
- ít nhất 1.000 dòng trong `features.master_features` và `target_labels`.

EIA có fallback Yahoo. Các ticker phụ có thể thiếu mà không chặn toàn bộ run,
nhưng độ phủ của chúng được kiểm tra trước khi vào sequence model.

## 5. Feature pipeline

Thứ tự SQL cố định:

1. price indicators;
2. momentum;
3. trend;
4. macro;
5. ratios;
6. target Open 1–10;
7. sliding windows;
8. EWMA;
9. seasonality/analogs;
10. market drivers;
11. master feature join.

`features.target_labels` không được join vào `features.master_features`.

## 6. Modeling

### Sequence models

- TiDE: multivariate historical exogenous.
- PatchTST: univariate theo implementation NeuralForecast hiện tại.
- N-HiTS: multivariate, multi-resolution.
- DLinear/NLinear: univariate linear sequence controls.

### Direct tabular models

- RidgeDirect;
- XGBoostDirect;
- LightGBMDirect;
- RidgeXGBoostBlend.

Mỗi horizon 1–10 có estimator riêng, target là
`log(future_open/current_close)`. Training dùng sliding window 1.260 phiên và
feature windows 5/10/21/63/126/252 phiên.

Thiết lập chuẩn:

- input window: 252 phiên;
- validation tail: 63 phiên;
- target transform: `log(gold_open)`;
- robust scaling;
- horizon train: 10;
- evaluation horizon: 1, 3, 5, 7, 10;
- exogenous coverage tối thiểu: 80%;
- rolling windows không shuffle.

Model được chọn theo mean rolling RMSE trên cùng sáu cửa sổ đánh giá.

## 7. Logging và artifact

Mỗi run có:

- human log `run.log`;
- structured JSON Lines `run.jsonl`;
- metadata/config/library versions;
- candidate leaderboard và per-horizon metrics;
- rolling/future predictions;
- model artifacts;
- stage duration, CPU, RAM, I/O và model size.

Run ID nối tất cả file với các bảng trong schema `forecasting`.

## 8. Reconciliation

Khi ngày dự báo đã có actual Open:

```powershell
python scripts/reconcile_open_forecasts.py
```

Lệnh cập nhật `actual_open`, absolute error, percentage error và
`evaluated_at` trong `forecasting.open_predictions`.

## 9. Xử lý lỗi

- API lỗi: xem `run.log`, `run.jsonl` và kết quả freshness.
- DB lỗi: kiểm tra `.env`, chạy `check_environment.py`.
- CFTC trống: kiểm tra current report và annual ZIP cache.
- Sequence chỉ còn ít dòng: xem `feature_columns.json`; feature độ phủ thấp phải
  nằm trong `excluded_sequence_exogenous_features`.
- Deep model chậm: giảm windows/steps để smoke test, không dùng kết quả đó làm
  benchmark chính thức.
- Forecast date lệch ngày nghỉ sàn: đây là lịch ước lượng; cần CME calendar nếu
  sử dụng vận hành.

## 10. Definition of Done

Một run đạt yêu cầu khi:

- `model_runs.status = completed`;
- có đúng 10 dòng forecast;
- có đủ sequence, direct tabular và fixed-weight ensemble candidates;
- có metric theo horizon;
- model artifacts reload/predict giống trước khi lưu;
- log và resource metrics tồn tại;
- `as_of_date` bằng phiên vàng hoàn tất mới nhất trong feature table.
