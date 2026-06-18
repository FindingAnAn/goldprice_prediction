# Gold Price Prediction

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
