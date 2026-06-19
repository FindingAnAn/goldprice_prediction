"""CLI for training, evaluation and prediction."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import LOGS_DIR, SUPPORTED_FORECAST_HORIZONS, TARGET_COLUMN
from src.modeling.autogluon_benchmark import benchmark_autogluon
from src.modeling.predict import load_best_model, predict_latest
from src.modeling.train import build_training_frame, evaluate_holdout_model, train_and_select_best
from src.utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)
PRICE_TARGET_COLUMNS = tuple(
    f"next_{horizon}_day_price"
    for horizon in SUPPORTED_FORECAST_HORIZONS
)


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
    train_parser.add_argument(
        "--target-col",
        choices=PRICE_TARGET_COLUMNS,
        default=TARGET_COLUMN,
        help="Future price target; defaults to the 7-session horizon",
    )
    evaluate_parser = subparsers.add_parser("evaluate", help="Evaluate a persisted model on a holdout split")
    evaluate_parser.add_argument(
        "--model-path",
        default="models/best_model_holdout.joblib",
        help="Train-only model used for leakage-safe holdout evaluation",
    )
    evaluate_parser.add_argument("--test-size", type=float, default=0.2, help="Chronological holdout ratio")
    evaluate_parser.add_argument(
        "--target-col",
        choices=PRICE_TARGET_COLUMNS,
        default=TARGET_COLUMN,
        help="Target used by the persisted model",
    )
    predict_parser = subparsers.add_parser("predict", help="Generate predictions for the newest rows")
    predict_parser.add_argument("--model-path", default="models/best_model.joblib", help="Path to the persisted model")
    predict_parser.add_argument("--latest-n", type=int, default=1, help="Number of latest rows to predict")
    predict_parser.add_argument("--no-persist", action="store_true", help="Do not write predictions to disk")

    autogluon_parser = subparsers.add_parser(
        "autogluon",
        help="Benchmark AutoGluon on an unseen chronological holdout",
    )
    autogluon_parser.add_argument(
        "--target-col",
        choices=PRICE_TARGET_COLUMNS,
        default=TARGET_COLUMN,
    )
    autogluon_parser.add_argument("--test-size", type=float, default=0.2)
    autogluon_parser.add_argument("--validation-size", type=float, default=0.2)
    autogluon_parser.add_argument("--time-limit", type=int, default=600)
    autogluon_parser.add_argument(
        "--presets",
        default="medium_quality",
        help="AutoGluon preset; medium_quality is the initial CPU benchmark",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    setup_logging(level=args.log_level, log_file=_resolve_log_file(args.command))
    logger.info("Starting modeling command", extra={"command": args.command})

    if args.command == "train":
        best = train_and_select_best(
            target_col=args.target_col,
            test_size=args.test_size,
            use_optuna=args.use_optuna,
            tuning_trials=args.tuning_trials,
        )
        logger.info("Training completed", extra={"model_name": best.name, "cv_rmse": best.cv_rmse, "test_rmse": best.test_rmse})
        print(
            f"Target: {args.target_col}\n"
            f"Best model: {best.name}\n"
            f"CV RMSE: {best.cv_rmse:.4f}\n"
            f"Test RMSE: {best.test_rmse:.4f}\n"
            f"Test MAE: {best.test_mae:.4f}\n"
            f"Test R2: {best.test_r2:.4f}\n"
            f"Params: {best.params}"
        )
        return

    if args.command == "evaluate":
        model = load_best_model(Path(args.model_path))
        frame = build_training_frame(target_col=args.target_col)
        metrics = evaluate_holdout_model(
            model,
            frame,
            target_col=args.target_col,
            test_size=args.test_size,
        )
        logger.info("Evaluation completed", extra={"rmse": metrics["rmse"]})
        print(f"Holdout RMSE: {metrics['rmse']:.4f}")
        return

    if args.command == "predict":
        model = load_best_model(Path(args.model_path))
        output = predict_latest(model=model, latest_n=args.latest_n, persist=not args.no_persist)
        logger.info("Prediction completed", extra={"rows": len(output)})
        print(output)
        return

    if args.command == "autogluon":
        result = benchmark_autogluon(
            target_col=args.target_col,
            test_size=args.test_size,
            validation_size=args.validation_size,
            time_limit=args.time_limit,
            presets=args.presets,
        )
        print(
            f"Target: {args.target_col}\n"
            f"AutoGluon best model: {result.model_name}\n"
            f"Holdout RMSE: {result.rmse:.4f}\n"
            f"Holdout MAE: {result.mae:.4f}\n"
            f"Holdout R2: {result.r2:.4f}\n"
            f"Model path: {result.model_path}"
        )
        return

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
