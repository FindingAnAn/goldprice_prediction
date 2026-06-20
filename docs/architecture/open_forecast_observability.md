# Ten-session gold open forecast and experiment observability

## Forecast contract

The workflow predicts the opening price for each of the next 10 trading
sessions:

`next_1_day_open` through `next_10_day_open`.

The prediction cutoff is after the latest completed gold session. Current
OHLCV and point-in-time-safe features are valid inputs. All future open targets
remain isolated in `features.target_labels`.

Forecast dates are estimates based on US federal business days. Exchange-
specific holiday or shortened-session calendars may differ. `forecast_step`
is the authoritative horizon identifier.

## Run command

```bash
python scripts/run_open_forecast.py
```

Each execution receives a stable `run_id` such as:

```text
gold_open_10d_20260620T081720Z_6d6aff47
```

The same identifier is written to logs, artifact metadata, model files and
PostgreSQL.

## Filesystem artifacts

Each run is stored under:

```text
data/predictions/open_10d/<run_id>/
```

Files:

- `run.log`: human-readable operational log;
- `run.jsonl`: structured JSON log with `run_id`, command and event fields;
- `metadata.json`: data hash, configuration, versions and artifact paths;
- `leaderboard.csv`: CV and chronological holdout metrics per candidate;
- `metrics.csv`: overall and horizon-specific metrics;
- `holdout_predictions.csv`: detailed historical holdout predictions;
- `open_predictions.csv`: 10 future opening-price predictions and intervals;
- `resource_metrics.csv`: CPU, RAM, IO and sample counts;
- `stage_metrics.csv`: duration and status of each workflow stage;
- `feature_columns.json`: ordered feature contract;
- `model.joblib` and `model_holdout.joblib`.

The latest production model is also copied to:

```text
models/open_forecast/latest_model.joblib
```

## PostgreSQL registry

The dedicated `forecasting` schema contains:

- `model_runs`;
- `model_candidates`;
- `model_metrics`;
- `open_predictions`;
- `stage_metrics`;
- `resource_metrics`.

The production prediction rows initially have no actual value. After new
sessions are ingested, run:

```bash
python scripts/reconcile_open_forecasts.py
```

This fills `actual_open`, absolute error, percentage error and live aggregate
metrics.

## Leakage controls

- Chronological train/holdout split.
- Purge gap of 10 sessions.
- `TimeSeriesSplit` with a 10-session gap.
- Every `next_*_day_open` column is blocked from model features.
- Model selection uses CV RMSE, not the final holdout.
- Production model is refit on all labeled data only after model selection.

## Current validated run

Run `gold_open_10d_20260620T081720Z_6d6aff47`:

- source cutoff: June 18, 2026;
- selected model: close-price persistence;
- CV RMSE: 30.61;
- chronological holdout RMSE: 90.03;
- holdout MAE: 51.34;
- holdout MAPE: 1.75%;
- runtime: about 101.85 seconds;
- peak process-tree RAM: about 419.50 MB;
- normalized average CPU: about 77.46% across 12 logical cores.

Persistence winning the CV benchmark means the more complex tabular models did
not provide stable incremental accuracy on this dataset. They remain recorded
in the leaderboard for auditability.
