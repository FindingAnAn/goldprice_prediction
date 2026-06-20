# Gold Price Prediction — Hướng Dẫn Chạy End-to-End

## Yêu Cầu Tiên Quyết

| Yêu cầu | Phiên bản tối thiểu |
|---------|---------------------|
| Python | 3.11+ |
| PostgreSQL | 14+ |
| psycopg2 | 2.9+ |
| pandas | 2.0+ |
| yfinance | 0.2+ |
| scikit-learn | 1.3+ |

### Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### Cấu hình `.env`

Tạo file `.env` tại root dự án (copy từ `.env.example` nếu có):

```env
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gold_prediction
DB_USER=postgres
DB_PASSWORD=your_password

# FRED API (lấy miễn phí tại https://fred.stlouisfed.org/docs/api/api_key.html)
FRED_API_KEY=your_fred_key

# EIA API (lấy miễn phí tại https://www.eia.gov/opendata/)
EIA_API_KEY=your_eia_key

# FreeGoldAPI (không cần key)
```

---

## Kiến Trúc Pipeline

```
Raw APIs                    PostgreSQL
─────────────────────       ────────────────────────────────────────────────
FreeGoldAPI (CSV)    ──┐
yfinance GC=F        ──┤→ raw.gold_prices
yfinance (OHLCV)     ──┤→ raw.yfinance_daily
FRED API (daily)     ──┤→ raw.fred_daily
FRED API (monthly)   ──┤→ raw.fred_monthly
EIA API (+fallback)  ──┘→ raw.eia_oil
                           │
                           ▼
                     staging.daily_master (JOIN + clean)
                           │
                           ▼
              ┌────────────────────────────────┐
              │  Feature Engineering (SQL)     │
              │  01: price_indicators          │
              │  02: momentum_indicators       │
              │  03: trend_indicators          │
              │  04: macro_features            │
              │  05: ratio_features            │
              │  06: target_labels  ← TÁCH     │
              │  07: sliding_windows           │
              │  09: ewma_features             │
              │  08: master_features (JOIN)    │
              └────────────────────────────────┘
                           │
                           ▼
                     Modeling (Python)
                     src/modeling/train.py
```

## Bước 0: Chuẩn Bị Database

### Tạo schemas và tables

```bash
# Kết nối PostgreSQL và chạy các schema scripts theo thứ tự
psql -U postgres -d gold_prediction -f sql/schema/01_raw_tables.sql
psql -U postgres -d gold_prediction -f sql/schema/02_staging_tables.sql
psql -U postgres -d gold_prediction -f sql/schema/03_feature_tables.sql
```

> **Lưu ý:** `03_feature_tables.sql` tạo đồng thời `features.ewma_features` và
> cập nhật `features.master_features` (không còn `gold_close`, `gold_open`).

---

## Bước 1: Ingestion — Fetch Dữ Liệu Raw

### Chạy toàn bộ pipeline từ Python

```python
# Từ project root
from src.pipelines.ingestion import run_ingestion_pipeline

report = run_ingestion_pipeline(
    start="2000-01-01",
    max_gap_days=3,
    z_threshold=5.0,
)
```

Kiểm tra freshness trước/sau ingestion:

```bash
python scripts/check_data_freshness.py
```

Yahoo Finance phải đạt latest completed market date. FRED/EIA có publication
lag tự nhiên; xem `docs/architecture/data_sources_freshness.md`.

### Hoặc chạy từng bước:

```python
from src.pipelines.ingestion import (
    prepare_database_schema,
    ingest_raw_sources,
    populate_staging_daily_master,
    run_cleaning,
)

# 1. Tạo schema (idempotent — an toàn khi chạy lại)
prepare_database_schema()

# 2. Fetch data từ 6 nguồn
gold_rows, yfinance_rows, fred_daily_rows, fred_monthly_rows, eia_rows = \
    ingest_raw_sources(start="2000-01-01")

# 3. Populate staging.daily_master
staging_rows = populate_staging_daily_master()

# 4. Cleaning: dedup, forward-fill, flag outliers
run_cleaning(max_gap_days=3, z_threshold=5.0)
```

### Hoặc chạy notebook `02_ingestion_api.ipynb`:

```bash
jupyter nbconvert --to notebook --execute notebooks/02_ingestion_api.ipynb
```

**Kết quả mong đợi:**
```
[INFO] Gold rows upserted : 6000+
[INFO] staging.daily_master: 6000+ rows
[INFO] yfinance ingestion — GC=F, DX-Y.NYB, ^GSPC, SI=F, ^VIX: OK
[INFO] FRED daily/monthly: OK
[INFO] EIA (WTI + Brent): OK
```

---

## Bước 2: Feature Engineering — Tính Features

### Chạy toàn bộ feature pipeline:

```python
from src.pipelines.ingestion import run_feature_engineering

feature_rows = run_feature_engineering()
# Kết quả: {'price_indicators': N, 'momentum_indicators': N, ..., 'ewma_features': N, 'master_features': N}
```

### Hoặc chạy trực tiếp SQL (dùng psql):

```bash
# Chạy toàn bộ feature pipeline một lệnh
psql -U postgres -d gold_prediction -f sql/pipelines/run_features.sql
```

Pipeline SQL theo thứ tự:

| Bước | File SQL | Bảng đích | Nội dung |
|------|----------|-----------|---------|
| 1 | `01_price_features.sql` | `features.price_indicators` | SMA 10/20/50/100/200, EMA, Bollinger Bands |
| 2 | `02_momentum_features.sql` | `features.momentum_indicators` | RSI-14, MACD, ROC-10, CCI-20, Stochastic |
| 3 | `03_trend_features.sql` | `features.trend_indicators` | ADX-14, Z-score 20d/60d |
| 4 | `04_macro_features.sql` | `features.macro_features` | DXY, Fed Funds, Yields, CPI, M2, VIX |
| 5 | `05_ratio_features.sql` | `features.ratio_features` | Gold/Silver, Gold/Oil, Real Yield |
| 6 | `06_target_labels.sql` | `features.target_labels` | next 1/3/5/7/10/21/30/63-session price, direction, %change |
| 7 | `07_sliding_window.sql` | `features.sliding_windows` | Rolling 5d/21d/63d/252d avg/max/min/std |
| 8 | `09_ewma_features.sql` | `features.ewma_features` | EWMA 7d/30d/90d/365d + crossover signals |
| 9 | `08_master_features.sql` | `features.master_features` | JOIN features + OHLCV phiên hiện tại, không có future targets |

**Kết quả mong đợi trong `master_features`:**

```
Cột features (ví dụ):
  gold_close, gold_open, gold_high,
  gold_low, gold_volume              ← OHLCV phiên hiện tại (hợp lệ sau close)
  sma_10 ... sma_200                 ← price indicators
  ema_10 ... ema_200                 ← exponential MA
  bb_upper, bb_lower, bb_width, bb_pct
  rsi_14, macd, macd_signal, ...     ← momentum
  adx_14, z_score_20, z_score_60     ← trend
  dxy_close, fed_funds_rate, ...     ← macro
  gold_silver_ratio, real_yield, ... ← ratios
  gold_avg_5d ... gold_avg_252d      ← sliding windows
  ewma_7d ... ewma_365d              ← EWMA prices
  ewma_vol_7d ... ewma_vol_365d      ← EWMA volumes
  price_vs_ewma_7d ... _365d         ← distance signals
  ewma_cross_7_30, _30_90, _90_365  ← crossover signals

KHÔNG có: next_*_day_*           ← target tương lai nằm ở bảng riêng
```

---

## Bước 3: EDA (Tuỳ Chọn)

```bash
jupyter nbconvert --to notebook --execute notebooks/03_eda.ipynb
```

---

## Bước 4: Training Models

### Cách 1 — Dùng `train.py` (khuyến nghị):

```bash
# Từ project root
python scripts/run_modeling.py train
```

Hoặc từ Python:

```python
from src.modeling.train import train_and_select_best

best = train_and_select_best(
    target_col="next_7_day_price",
    test_size=0.2,
    random_state=42,
    use_optuna=True,
    tuning_trials=50,
)
print(f"Best model: {best.name}, CV-RMSE: {best.cv_rmse:.2f}, Test-RMSE: {best.test_rmse:.2f}")
```

### Cách 2 — Notebook `04_modeling.ipynb`:

```bash
jupyter nbconvert --to notebook --execute notebooks/04_modeling.ipynb
```

> **Anti-leakage trong training:**
> - OHLCV phiên hiện tại hợp lệ vì cutoff dự báo là sau market close
> - `infer_feature_columns()` loại toàn bộ `next_*_day_*`, không chỉ target đang dự báo
> - FRED monthly chưa có release-date/vintage bị chặn khỏi model
> - FRED daily dùng giá trị có ngày quan sát trước ngày dự báo; market yields lấy từ Yahoo trong phiên hiện tại
> - Optuna dùng `TimeSeriesSplit` CV trên **train set only** — X_test không bị nhìn thấy khi tune
> - Target `t+7` dùng purge gap 7 phiên giữa train/test và giữa các CV fold
> - Scaler `fit_transform` trên train, `transform` trên test

### AutoGluon benchmark (tùy chọn)

```bash
pip install -r requirements-autogluon.txt
python scripts/run_modeling.py autogluon --time-limit 600
```

AutoGluon dùng chronological train/validation/test. Chỉ kết luận tối ưu hơn
khi RMSE/MAE trên final holdout thấp hơn pipeline chuẩn; không so sánh bằng
training score.

### Seasonality, horizon và deep forecasting

```bash
python scripts/analyze_similarity.py
python scripts/benchmark_horizons.py
pip install -r requirements-deep-forecasting.txt
python scripts/benchmark_deep_models.py --models neuralforecast
```

Chi tiết phương pháp và kết quả:
`docs/architecture/seasonality_horizon_benchmark.md`.

### Dự báo giá open cho 10 phiên tiếp theo

```bash
python scripts/run_open_forecast.py
```

Mỗi lần chạy tạo một `run_id`, lưu toàn bộ log và artifacts tại
`data/predictions/open_10d/<run_id>/`, đồng thời ghi kết quả vào schema
PostgreSQL `forecasting`.

Khi dữ liệu thực tế của các phiên tương lai đã được ingest:

```bash
python scripts/reconcile_open_forecasts.py
```

Chi tiết: `docs/architecture/open_forecast_observability.md`.

**Benchmark gần nhất (chronological split, purge gap 7 phiên):**

```
model               CV RMSE   Test RMSE   Test MAE
persistence           36.60       99.05      61.19
return_catboost        44.42      108.78      69.22
return_extra_trees     48.73      106.22      66.84
return_lasso           63.88       96.59      60.70
```

Tree/boosting models learn the 7-session return and reconstruct future price,
because direct level prediction cannot extrapolate reliably under price drift.
Selection still uses CV only; the lower test RMSE of `return_lasso` is not used
to choose it after seeing the holdout.

Model artifacts lưu tại `models/`:
```
models/
├── best_model.joblib
├── best_model_holdout.joblib
└── best_model_<selected_name>.joblib

data/predictions/
├── model_leaderboard.csv
└── permutation_importance.csv
```

`best_model.joblib` được refit trên toàn bộ nhãn để dự báo production.
Chỉ dùng `best_model_holdout.joblib` khi báo cáo holdout metric.

---

## Bước 5: Evaluation

```bash
jupyter nbconvert --to notebook --execute notebooks/05_evaluation.ipynb
```

---

## Bước 6: Monitoring Dashboard (Tuỳ Chọn)

```bash
jupyter nbconvert --to notebook --execute notebooks/06_monitoring_dashboard.ipynb
```

---

## Chạy Toàn Bộ Pipeline Một Lệnh

```python
# run_all.py — chạy từ project root
from src.pipelines.ingestion import run_ingestion_pipeline
from src.modeling.train import train_and_select_best

# Bước 1–2: Ingestion + Feature Engineering
report = run_ingestion_pipeline(start="2000-01-01")

# Bước 3: Training
best = train_and_select_best(
    use_optuna=True,
    tuning_trials=50,
)
print(f"Pipeline hoàn tất. Best: {best.name} | Test-RMSE: {best.test_rmse:.2f}")
```

---

## Xử Lý Lỗi Thường Gặp

| Lỗi | Nguyên nhân | Fix |
|-----|-------------|-----|
| `ConnectionError: HTTP 429 FreeGoldAPI` | Rate limit | Chờ 60s rồi chạy lại |
| Không có `FRED_API_KEY` | Chưa cấu hình key | Pipeline tự dùng public FRED CSV |
| `EIA API error` | Key thiếu/hết hạn | Script tự fallback sang yfinance `CL=F`, `BZ=F` |
| PostgreSQL password authentication failed | Thiếu/sai `DB_PASSWORD` hoặc `DB_NAME` | Tạo `.env` đúng theo `.env.example` |
| `relation "features.ewma_features" does not exist` | Schema chưa được tạo | Chạy lại `sql/schema/03_feature_tables.sql` |
| Thiếu `gold_close` trong `master_features` | Schema/feature pipeline cũ | Chạy lại schema và `scripts/rebuild_features.py` |
| `staging.daily_master: 0 rows` | Chưa populate staging | Chạy `populate_staging_daily_master()` |

---

## EWMA Features — Chi Tiết

Bảng `features.ewma_features` chứa 15 cột:

| Cột | Ý nghĩa | Window (calendar) | Alpha |
|-----|---------|------------------|-------|
| `ewma_7d` | EWMA giá vàng 7 ngày | ≈ 5 trading days | 2/6 ≈ 0.333 |
| `ewma_30d` | EWMA giá vàng 30 ngày | ≈ 21 trading days | 2/22 ≈ 0.091 |
| `ewma_90d` | EWMA giá vàng 90 ngày | ≈ 63 trading days | 2/64 ≈ 0.031 |
| `ewma_365d` | EWMA giá vàng 365 ngày | ≈ 252 trading days | 2/253 ≈ 0.008 |
| `ewma_vol_7d/30d/90d/365d` | EWMA volume tương ứng | — | — |
| `price_vs_ewma_7d/30d/90d/365d` | % khoảng cách giá vs EWMA | — | >0 = bullish |
| `ewma_cross_7_30` | +1 nếu ewma_7d > ewma_30d | — | momentum tín hiệu |
| `ewma_cross_30_90` | +1 nếu ewma_30d > ewma_90d | — | trend tín hiệu |
| `ewma_cross_90_365` | +1 nếu ewma_90d > ewma_365d | — | long-term trend |

---

## Cấu Trúc File Liên Quan

```
gold_time_prediction/
├── .env                              ← API keys + DB credentials
├── sql/
│   ├── schema/
│   │   ├── 01_raw_tables.sql         ← Tạo raw.* tables
│   │   ├── 02_staging_tables.sql     ← Tạo staging.daily_master
│   │   └── 03_feature_tables.sql     ← Tạo features.* tables (bao gồm ewma_features)
│   ├── features/
│   │   ├── 01_price_features.sql
│   │   ├── 02_momentum_features.sql
│   │   ├── 03_trend_features.sql
│   │   ├── 04_macro_features.sql
│   │   ├── 05_ratio_features.sql
│   │   ├── 06_target_labels.sql      ← next_*_day_price (TARGET ONLY)
│   │   ├── 07_sliding_window.sql
│   │   ├── 08_master_features.sql    ← JOIN features + current OHLCV, không có target
│   │   └── 09_ewma_features.sql      ← EWMA 7/30/90/365d
│   └── pipelines/
│       └── run_features.sql          ← Orchestrate bước 1–9
├── src/
│   ├── data/
│   │   ├── ingestion/
│   │   │   ├── freegold_ingestion.py ← FreeGoldAPI + yfinance GC=F
│   │   │   ├── yfinance_ingestion.py ← DXY, Silver, Oil, SP500, VIX
│   │   │   ├── fred_ingestion.py     ← FRED daily + monthly
│   │   │   └── eia_ingestion.py      ← WTI + Brent (EIA / yfinance fallback)
│   │   └── preprocessing/
│   │       └── cleaning.py           ← dedup, ffill, outlier flagging
│   ├── modeling/
│   │   └── train.py                  ← Ridge, RF, XGB, LGBM, CatBoost, Optuna+XGB
│   └── pipelines/
│       ├── ingestion.py              ← Orchestrate toàn bộ ingestion
│       └── eda_data.py               ← Load helpers cho EDA + modeling
└── notebooks/
    ├── 01_env_check.ipynb
    ├── 02_ingestion_api.ipynb
    ├── 03_eda.ipynb
    ├── 04_modeling.ipynb             ← Interactive exploration
    ├── 05_evaluation.ipynb
    └── 06_monitoring_dashboard.ipynb
```
