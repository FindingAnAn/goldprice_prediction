# Modeling Workflow

Use `scripts/run_modeling.py` as the single CLI for the modeling stage.

## Commands

Train and tune candidate models:

```bash
python scripts/run_modeling.py train --use-optuna --tuning-trials 20
```

The default target is `next_7_day_price`: one direct forecast for the price
after seven trading observations.

Benchmark AutoGluon without exposing the final holdout during tuning:

```bash
pip install -r requirements-autogluon.txt
python scripts/run_modeling.py autogluon --time-limit 600
```

Evaluate the persisted model on a chronological holdout split:

```bash
python scripts/run_modeling.py evaluate --model-path models/best_model.joblib
```

Generate the latest prediction and persist it to `data/predictions/`:

```bash
python scripts/run_modeling.py predict --latest-n 1
```

## Notes

- `src/modeling/train.py` is the canonical training implementation.
- `src/modeling/predict.py` exposes a frame-based API for tests and batch inference.
- AutoGluon is accepted only if its final chronological holdout metrics beat
  the canonical pipeline under the same target and split policy.
- Every future target column is excluded from model inputs.
- Seven observations are purged between train/test and CV folds.
- Legacy duplicate ingestion entrypoints were removed in favor of the canonical pipeline.
