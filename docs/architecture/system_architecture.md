# System Architecture

## Phạm vi

Hệ thống là batch forecasting pipeline cho dữ liệu daily. PostgreSQL xử lý
storage/feature engineering; Python điều phối API, training và observability.

```mermaid
flowchart LR
    A["Yahoo / FreeGold / FRED / CFTC / EIA"] --> B["raw schema"]
    B --> C["staging.daily_master"]
    C --> D["SQL feature tables"]
    D --> E["features.master_features"]
    C --> F["features.target_labels"]
    E --> G["Persistence baseline"]
    E --> H["TiDE / PatchTST / N-HiTS"]
    F --> G
    F --> H
    G --> I["Rolling evaluation + selection"]
    H --> I
    I --> J["10-session Open forecast"]
    J --> K["Filesystem artifacts"]
    J --> L["forecasting schema"]
```

## Thành phần

| Layer | Trách nhiệm |
|---|---|
| `config/` | Cấu hình tập trung, paths, tickers, model constants |
| `src/data/ingestion/` | API clients, normalization, raw upsert |
| `src/data/storage/` | PostgreSQL connection, schema/SQL runners |
| `sql/schema/` | DDL raw, staging, features, forecasting |
| `sql/features/` | Feature và target generation |
| `src/pipelines/` | Orchestration, validation, EDA, environment checks |
| `src/modeling/` | Leakage guards, baseline, sequence models, explanations |
| `src/experiments/` | Run ID, file/DB persistence, metadata |
| `scripts/` | CLI entrypoints |

## Quyết định kiến trúc

- Không dùng Spark: dữ liệu daily từ 2010 chỉ vài nghìn dòng.
- Không dùng Polars trong production path: bottleneck là network, SQL và deep
  training; đổi DataFrame engine không tạo lợi ích đáng kể ở quy mô này.
- Không import logic production từ `scripts/`; scripts chỉ là thin CLI.
- Không giữ song song stack tabular target cũ; một forecast contract duy nhất
  giảm drift giữa code, SQL và tài liệu.
- Feature SQL có thứ tự cố định để reproducible.
- Forecasting history tách schema và không bị full refresh xóa.

## Boundary

- Cutoff: sau phiên hiện tại.
- Prediction unit: một trading session.
- Target: vector 10 Open.
- Forecast date: business-day estimate, không phải CME calendar chính thức.
- Deployment hiện tại: batch/local; chưa có scheduler hay serving API.
