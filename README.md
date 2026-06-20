# Gold Open Forecast

Pipeline dự báo giá **Open của vàng cho 10 phiên giao dịch tiếp theo**. Dữ liệu
được ingest lại từ `2010-01-01`, lưu trong PostgreSQL, tạo feature bằng SQL,
benchmark theo thời gian và lưu đầy đủ log, metric, model, dự báo và tài nguyên.

## Contract hiện tại

- Cutoff dự báo: sau khi phiên vàng hiện tại đã hoàn tất.
- Target: `next_1_day_open` đến `next_10_day_open`.
- Baseline: giá Close hiện tại lặp lại cho 10 phiên.
- Mô hình sequence bắt buộc: TiDE, PatchTST và N-HiTS.
- Chọn model: RMSE trung bình trên rolling windows tại horizon 1, 3, 5, 7, 10.
- Lịch sử: từ `2010-01-01` để đồng bộ CFTC Disaggregated COT.
- Mỗi lần chạy full pipeline: truncate `raw`, `staging`, `features`; schema
  `forecasting` được giữ lại để bảo toàn lịch sử thí nghiệm.

## Cài đặt

Yêu cầu Python 3.11+, PostgreSQL và biến môi trường:

```dotenv
DB_HOST=127.0.0.1
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=...
DB_NAME=...
FRED_API_KEY=...
EIA_API_KEY=...
```

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`EIA_API_KEY` không bắt buộc; pipeline dùng `CL=F` và `BZ=F` khi EIA không khả
dụng. `FRED_API_KEY` cần thiết cho dữ liệu FRED.

## Chạy pipeline

Kiểm tra môi trường và độ mới dữ liệu:

```powershell
python scripts/check_environment.py
python scripts/check_data_freshness.py
```

Ingest lại toàn bộ dữ liệu từ 2010 và rebuild feature:

```powershell
python scripts/run_ingestion.py
```

Chạy toàn bộ ingest, benchmark, chọn model và dự báo Open 10 phiên:

```powershell
python scripts/run_open_forecast.py
```

Tham số giảm thời gian smoke test:

```powershell
python scripts/run_open_forecast.py --deep-windows 2 --deep-max-steps 2
```

Các lệnh độc lập:

```powershell
# Rebuild staging/features từ raw hiện có, không gọi API
python scripts/rebuild_features.py

# EDA và phân tích seasonal/regime similarity
python scripts/run_eda.py --no-plots
python scripts/analyze_dataset.py
python scripts/analyze_similarity.py

# Benchmark sequence, không ingest lại
python scripts/benchmark_deep_models.py --n-windows 6 --max-steps 100

# Điền actual Open cho các dự báo đã đến hạn
python scripts/reconcile_open_forecasts.py
```

Kiểm tra code:

```powershell
pytest -q
```

## Dữ liệu đầu vào

| Nguồn | Vai trò |
|---|---|
| Yahoo Finance | GC=F, DXY, silver, equities, volatility, rates và ETF proxies |
| FreeGoldAPI | Lịch sử/fallback giá vàng |
| FRED | yield, real yield, inflation expectation, EPU và credit spread |
| CFTC | Vị thế COMEX gold theo tuần, join từ `available_date` |
| EIA | WTI và Brent; Yahoo Finance là fallback |

Pipeline chỉ lấy Yahoo đến phiên Mỹ đã hoàn tất an toàn. CFTC dùng ngày phát
hành bảo thủ `report_date + 3 ngày`. FRED monthly bị loại khỏi model vì chưa có
vintage/release timestamp point-in-time.

## Feature chính

- OHLCV, return, gap, range và close location.
- SMA, EMA, Bollinger, RSI, MACD, ADX, ROC, CCI, stochastic.
- Sliding windows 5/21/63/252 phiên và EWMA 7/30/90/365 ngày.
- DXY, nominal/real yield, VIX, S&P 500, silver, oil và các tỷ lệ liên thị trường.
- GLD/TLT/UUP/TIP/HYG return và GLD volume z-score.
- Economic Policy Uncertainty và CFTC positioning.
- Month/quarter/year progress, same-month, same-quarter, day-of-year analog và
  market-regime analog.

Sequence model chỉ nhận feature có độ phủ tối thiểu 80%. Credit spread
`BAMLH0A0HYM2` vẫn được lưu để phân tích nhưng không ép vào sequence model vì
FRED hiện chỉ phân phối khoảng ba năm lịch sử cho series này.

## Output

Mỗi run có thư mục:

```text
data/predictions/open_10d/<run_id>/
├── run.log
├── run.jsonl
├── metadata.json
├── leaderboard.csv
├── metrics.csv
├── open_predictions.csv
├── holdout_predictions.csv
├── deep_model_metrics.csv
├── deep_model_predictions.csv
├── deep_model_future_predictions.csv
├── resource_metrics.csv
├── stage_metrics.csv
├── feature_columns.json
├── model.joblib
└── deep_models/
```

Kết quả cũng được lưu trong schema PostgreSQL `forecasting`:

- `model_runs`
- `model_candidates`
- `model_metrics`
- `open_predictions`
- `stage_metrics`
- `resource_metrics`

`open_predictions.csv` và bảng DB gồm giá dự báo, khoảng sai số 80%/95%, chênh
lệch tuyệt đối/phần trăm so với Close hiện tại, hướng tăng/giảm/đi ngang và ba
lý do kinh tế. Các lý do là **evidence theo rule**, không phải causal attribution
hay SHAP.

## Kiểm soát data leakage

- Target nằm riêng trong `features.target_labels`, không nằm trong
  `features.master_features`.
- Split chronological có purge gap 10 phiên.
- Rolling validation không shuffle.
- Feature future có prefix `next_<n>_day_` bị chặn tự động.
- CFTC chỉ join sau `available_date`.
- Seasonal analog chỉ dùng quan sát ít nhất một năm trước ngày dự báo.
- FRED monthly/revised fields nằm trong danh sách cấm model.

Xem chi tiết tại [data_leakage_audit.md](docs/architecture/data_leakage_audit.md).

## Cấu trúc

```text
config/                  cấu hình tập trung
scripts/                 CLI entrypoints
sql/schema/              DDL PostgreSQL
sql/features/            feature engineering SQL
src/data/ingestion/      API clients
src/data/storage/        PostgreSQL utilities
src/modeling/            baseline, sequence benchmark, explanation
src/pipelines/           ingestion, EDA, environment checks
src/experiments/         run tracking và artifact persistence
tests/unit/              unit tests
docs/architecture/       thiết kế và audit
docs/conventions/        chuẩn engineering của project
```

Tài liệu vận hành: [PIPELINE_GUIDE.md](docs/PIPELINE_GUIDE.md).
Kiến trúc: [system_architecture.md](docs/architecture/system_architecture.md).

## Giới hạn

- Dự báo giá vàng là bài toán nhiễu cao; persistence là baseline bắt buộc và có
  thể thắng deep model trong một số giai đoạn.
- `forecast_date` dùng US federal business day, chưa phải lịch CME chính thức.
- Daily FRED được lag một ngày nhưng chưa dùng ALFRED vintage; vẫn còn revision
  risk cho nghiên cứu lịch sử.
- Không dùng Spark: dữ liệu daily khoảng vài nghìn dòng, overhead phân tán không
  hợp lý. Pandas đủ cho orchestration; phần nặng nằm ở PostgreSQL và PyTorch.
