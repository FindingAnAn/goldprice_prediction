# Modeling Workflow

Use `scripts/run_modeling.py` as the single CLI for the modeling stage.

## Commands

Train and tune candidate models:

```bash
python scripts/run_modeling.py train --use-optuna --tuning-trials 20
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
- Legacy duplicate ingestion entrypoints were removed in favor of the canonical pipeline.