# Open Forecast Observability

## Run identity

Run ID dạng:

```text
gold_open_10d_YYYYMMDDTHHMMSSZ_<8-hex>
```

Run ID liên kết log, model, CSV và các bảng DB.

## Logging

- `run.log`: human-readable.
- `run.jsonl`: structured event log.
- Context: run ID, command, stage, model, duration và error type.
- Exception dùng stack trace và run được chuyển sang `failed`.

## Database

| Table | Nội dung |
|---|---|
| `forecasting.model_runs` | status, config, hash, model chọn, runtime |
| `forecasting.model_candidates` | candidate, metric tổng hợp, artifact |
| `forecasting.model_metrics` | metric theo split/horizon |
| `forecasting.open_predictions` | 10 forecast và actual/error sau reconcile |
| `forecasting.stage_metrics` | thời gian từng stage |
| `forecasting.resource_metrics` | RAM, CPU, I/O, size, throughput |

## Filesystem

Mỗi run lưu dưới `data/predictions/open_10d/<run_id>/`. Runtime outputs được
git-ignore; source code không phụ thuộc vào artifact cũ trong repository.

## Resource metrics

- peak/average RSS;
- average/max CPU;
- aggregate CPU across logical cores;
- read/write bytes;
- model and deep-model size;
- prediction rows per second.

## Artifact verification

Trước khi complete:

- reload Joblib baseline và so prediction bằng tolerance chặt;
- reload từng NeuralForecast artifact;
- so future prediction với giá trị trước khi lưu.

Nếu verification lỗi, run không được đánh dấu completed.
