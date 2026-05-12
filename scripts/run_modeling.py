"""CLI for training, evaluation and prediction."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import LOGS_DIR
from src.modeling.predict import load_best_model, predict_latest
from src.modeling.train import build_training_frame, evaluate_holdout_model, train_and_select_best
from src.utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


def _resolve_log_file(command: str) -> Path:
    return LOGS_DIR / "modeling" / f"run_modeling_{command}.log"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train, evaluate and predict with gold-time models")
    parser.add_argument("--log-level", default=None, help="Override LOG_LEVEL for this run")

    subparsers = parser.add_subparsers(dest="command", required=True)

    train_parser = subparsers.add_parser("train", help="Train candidate models and persist the best one")
    train_parser.add_argument("--use-optuna", action="store_true", help="Enable Optuna tuning")
    train_parser.add_argument("--tuning-trials", type=int, default=10, help="Number of Optuna trials per model")
    train_parser.add_argument("--test-size", type=float, default=0.2, help="Chronological holdout ratio")

    evaluate_parser = subparsers.add_parser("evaluate", help="Evaluate a persisted model on a holdout split")
    evaluate_parser.add_argument("--model-path", default="models/best_model.joblib", help="Path to the persisted model")
    evaluate_parser.add_argument("--test-size", type=float, default=0.2, help="Chronological holdout ratio")

    predict_parser = subparsers.add_parser("predict", help="Generate predictions for the newest rows")
    predict_parser.add_argument("--model-path", default="models/best_model.joblib", help="Path to the persisted model")
    predict_parser.add_argument("--latest-n", type=int, default=1, help="Number of latest rows to predict")
    predict_parser.add_argument("--no-persist", action="store_true", help="Do not write predictions to disk")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    setup_logging(level=args.log_level, log_file=_resolve_log_file(args.command))
    logger.info("Starting modeling command", extra={"command": args.command})

    if args.command == "train":
        best = train_and_select_best(
            test_size=args.test_size,
            use_optuna=args.use_optuna,
            tuning_trials=args.tuning_trials,
        )
        logger.info("Training completed", extra={"model_name": best.name, "cv_rmse": best.cv_rmse, "test_rmse": best.test_rmse})
        print(
            f"Best model: {best.name}\n"
            f"CV RMSE: {best.cv_rmse:.4f}\n"
            f"Test RMSE: {best.test_rmse:.4f}\n"
            f"Params: {best.params}"
        )
        return

    if args.command == "evaluate":
        model = load_best_model(Path(args.model_path))
        frame = build_training_frame()
        metrics = evaluate_holdout_model(model, frame, test_size=args.test_size)
        logger.info("Evaluation completed", extra={"rmse": metrics["rmse"]})
        print(f"Holdout RMSE: {metrics['rmse']:.4f}")
        return

    if args.command == "predict":
        model = load_best_model(Path(args.model_path))
        output = predict_latest(model=model, latest_n=args.latest_n, persist=not args.no_persist)
        logger.info("Prediction completed", extra={"rows": len(output)})
        print(output)
        return

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
