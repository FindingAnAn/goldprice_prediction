# Gold Price Prediction

<<<<<<< HEAD
Dự báo trực tiếp giá đóng cửa vàng sau **7 phiên giao dịch** (`t+7`).
Target mặc định là `next_7_day_price`; đây là một giá trị tại phiên thứ 7,
không phải chuỗi 7 giá trị liên tiếp.

## Modeling

```powershell
# Pipeline pandas
python scripts/run_modeling.py train

# Kiểm tra ngày mới nhất từ API và PostgreSQL
python scripts/check_data_freshness.py

# AutoGluon benchmark trên chronological holdout riêng
pip install -r requirements-autogluon.txt
python scripts/run_modeling.py autogluon --time-limit 600
```

Pipeline áp dụng:

- chronological train/test split;
- purge gap bằng forecast horizon (7 phiên);
- `TimeSeriesSplit(gap=7)` khi cross-validation;
- loại toàn bộ cột `next_*_day_*` khỏi features.
- loại FRED monthly chưa có release-date/vintage khỏi model.

Xem [docs/PIPELINE_GUIDE.md](docs/PIPELINE_GUIDE.md) để chạy ingestion,
feature engineering và modeling end-to-end.
Chi tiết leakage: [data_leakage_audit.md](docs/architecture/data_leakage_audit.md).
Chi tiết freshness API: [data_sources_freshness.md](docs/architecture/data_sources_freshness.md).
=======
Dự án xây dựng pipeline end-to-end để thu thập dữ liệu thị trường, tạo đặc
trưng và dự báo giá vàng ngày kế tiếp. Dữ liệu được lấy từ Yahoo Finance,
FRED, EIA và FreeGoldAPI, lưu trong PostgreSQL, sau đó được xử lý bằng SQL và
huấn luyện bằng các mô hình machine learning.

## Tính năng chính

- Thu thập dữ liệu giá vàng, bạc, dầu, chỉ số USD, chứng khoán, lãi suất,
  lạm phát và biến động thị trường.
- Lưu dữ liệu theo ba lớp PostgreSQL: `raw`, `staging` và `features`.
- Làm sạch dữ liệu, loại bản ghi trùng, forward-fill khoảng trống ngắn và
  đánh dấu outlier.
- Tạo các nhóm đặc trưng kỹ thuật và kinh tế vĩ mô bằng SQL:
  SMA, EMA, Bollinger Bands, RSI, MACD, ADX, rolling window, EWMA và các tỷ lệ.
- Huấn luyện và so sánh Ridge, Lasso, Random Forest, XGBoost và LightGBM.
- Hỗ trợ tối ưu siêu tham số bằng Optuna với `TimeSeriesSplit`.
- Đánh giá theo chronological holdout và xuất dự báo ra CSV.
- Cung cấp notebook cho từng giai đoạn phân tích.

## Kiến trúc pipeline

```text
Yahoo Finance / FRED / EIA / FreeGoldAPI
                    |
                    v
            PostgreSQL raw.*
                    |
                    v
        staging.daily_master
                    |
          Cleaning + validation
                    |
                    v
          Feature Engineering
             features.*
                    |
                    v
       Training / Evaluation / Prediction
                    |
                    v
       models/ + data/predictions/
```

`features.master_features` chỉ chứa biến đầu vào. Giá đóng/mở cửa và các
nhãn tương lai được tách sang `features.target_labels` để hạn chế data leakage.

## Yêu cầu

- Python 3.11 trở lên
- PostgreSQL 14 trở lên
- `pip`
- API key của FRED
- API key của EIA (không bắt buộc, pipeline có thể fallback sang Yahoo Finance)

## Cài đặt

```bash
git clone <repository-url>
cd goldprice_prediction

python -m venv .venv
```

Kích hoạt môi trường ảo:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux/macOS
source .venv/bin/activate
```

Cài đặt thư viện:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Cấu hình

Sao chép file cấu hình mẫu:

```powershell
Copy-Item .env.example .env
```

Trên Linux/macOS:

```bash
cp .env.example .env
```

Cập nhật các biến trong `.env`:

```env
FRED_API_KEY=your_fred_api_key
EIA_API_KEY=your_eia_api_key

DB_HOST=127.0.0.1
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=gold_prediction
```

Tạo database trước khi chạy pipeline, ví dụ:

```sql
CREATE DATABASE gold_prediction;
```

## Chạy nhanh

Tất cả lệnh dưới đây được chạy từ thư mục gốc của project.

### 1. Kiểm tra môi trường

```bash
python scripts/check_environment.py
```

Lệnh này kiểm tra API key, kết nối PostgreSQL, trạng thái bảng và các thư mục
dữ liệu cần thiết.

### 2. Thu thập dữ liệu và tạo đặc trưng

```bash
python scripts/run_ingestion.py
```

Pipeline sẽ tự động:

1. Tạo schema và bảng PostgreSQL.
2. Thu thập dữ liệu từ các nguồn bên ngoài.
3. Tạo `staging.daily_master`.
4. Làm sạch dữ liệu.
5. Chạy toàn bộ SQL feature engineering.

Mốc dữ liệu mặc định bắt đầu từ `2000-01-01`, được cấu hình tại
`config/settings.py`.

### 3. Phân tích dữ liệu

```bash
python scripts/run_eda.py
```

Lệnh trên đọc dữ liệu từ PostgreSQL, in thống kê và hiển thị các biểu đồ EDA.

### 4. Huấn luyện mô hình

Huấn luyện các mô hình với cấu hình mặc định:

```bash
python scripts/run_modeling.py train
```

Huấn luyện kèm Optuna:

```bash
python scripts/run_modeling.py train --use-optuna --tuning-trials 20
```

Mô hình tốt nhất theo cross-validation RMSE được lưu tại:

```text
models/best_model.joblib
models/best_model_<model_name>.joblib
```

### 5. Đánh giá mô hình

```bash
python scripts/run_modeling.py evaluate \
  --model-path models/best_model.joblib
```

Trên PowerShell có thể viết trên một dòng:

```powershell
python scripts/run_modeling.py evaluate --model-path models/best_model.joblib
```

### 6. Dự báo

Dự báo cho dòng dữ liệu mới nhất:

```bash
python scripts/run_modeling.py predict --latest-n 1
```

Dự báo nhiều dòng và không ghi file:

```bash
python scripts/run_modeling.py predict --latest-n 5 --no-persist
```

Mặc định kết quả được lưu dưới dạng:

```text
data/predictions/predictions_<UTC-timestamp>.csv
```

## Notebook

Các notebook mô tả từng giai đoạn:

| Notebook | Nội dung |
|---|---|
| `01_env_check.ipynb` | Kiểm tra môi trường |
| `02_ingestion_api.ipynb` | Thu thập dữ liệu |
| `03_eda.ipynb` | Exploratory Data Analysis |
| `04_modeling.ipynb` | Huấn luyện mô hình |
| `05_evaluation.ipynb` | Đánh giá mô hình |
| `06_monitoring_dashboard.ipynb` | Dashboard theo dõi |

Khởi chạy Jupyter:

```bash
pip install notebook
jupyter notebook
```

## Kiểm thử

Cài `pytest` nếu môi trường chưa có:

```bash
pip install pytest
```

Chạy toàn bộ unit test:

```bash
python -m pytest tests -v
```

## Cấu trúc thư mục

```text
goldprice_prediction/
|-- config/                 # Cấu hình nguồn dữ liệu và ứng dụng
|-- data/
|   |-- raw/                # Dữ liệu thô hoặc file trung gian
|   |-- processed/          # Dữ liệu đã xử lý
|   |-- features/           # Feature dataset dạng file
|   `-- predictions/        # Kết quả dự báo
|-- docs/                   # Tài liệu pipeline, kiến trúc và convention
|-- models/                 # Model artifacts
|-- notebooks/              # Notebook theo từng giai đoạn
|-- scripts/                # CLI entry points
|-- sql/
|   |-- schema/             # Khởi tạo raw, staging và features
|   |-- features/           # SQL feature engineering
|   `-- pipelines/          # Điều phối SQL pipeline
|-- src/
|   |-- data/               # Ingestion, preprocessing và PostgreSQL client
|   |-- modeling/           # Training, evaluation và prediction
|   |-- pipelines/          # Pipeline cấp cao
|   `-- utils/              # Config loader và logging
|-- tests/                  # Unit tests
|-- .env.example
`-- requirements.txt
```

## Nguồn dữ liệu

| Nguồn | Dữ liệu |
|---|---|
| Yahoo Finance | Vàng, bạc, dầu, DXY, S&P 500, VIX, lợi suất và ETF |
| FRED | Lãi suất, CPI, M2, thất nghiệp, yield curve và dữ liệu vĩ mô |
| EIA | Giá dầu WTI và Brent |
| FreeGoldAPI | Dữ liệu giá vàng và tỷ lệ vàng/bạc |

## Lưu ý về mô hình

- Dữ liệu train/test được chia theo thời gian, không shuffle.
- Optuna chỉ tối ưu trên tập train bằng `TimeSeriesSplit`.
- Mô hình tốt nhất được chọn theo CV RMSE; test RMSE dùng để báo cáo trên
  chronological holdout.
- Pipeline mặc định dự báo `next_1_day_price`.
- Model artifact phụ thuộc vào thứ tự feature hiện tại trong
  `features.master_features`; cần huấn luyện lại sau khi thay đổi schema feature.

## Lỗi thường gặp

### Không kết nối được PostgreSQL

Kiểm tra `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` trong
`.env` và bảo đảm PostgreSQL đang chạy.

### Thiếu FRED API key

Đăng ký key tại
[FRED API](https://fred.stlouisfed.org/docs/api/api_key.html), sau đó cập nhật
`FRED_API_KEY` trong `.env`.

### EIA API lỗi

Kiểm tra key tại [EIA Open Data](https://www.eia.gov/opendata/). Khi EIA không
khả dụng, pipeline sẽ thử dùng các ticker dầu trên Yahoo Finance.

### Bảng feature chưa tồn tại hoặc chưa có dữ liệu

Chạy lại:

```bash
python scripts/run_ingestion.py
```

Tài liệu chi tiết hơn có tại `docs/PIPELINE_GUIDE.md` và
`docs/architecture/modeling_workflow.md`.
>>>>>>> b8e359e6a7a343026c5ea0e5de9bb2a67ff928da
