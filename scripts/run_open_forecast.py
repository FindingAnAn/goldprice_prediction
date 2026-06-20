"""Train, evaluate and persist the next-10-session gold open forecast."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import time

import joblib
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import (
    OPEN_FORECAST_CV_SPLITS,
    OPEN_FORECAST_HORIZON,
    OPEN_FORECAST_MODEL_CONFIG,
    OPEN_FORECAST_RANDOM_SEED,
    OPEN_FORECAST_TEST_SIZE,
    OPEN_TARGET_COLUMNS,
    SQL_DIR,
)
from src.data.storage.postgres_client import run_schema_pipeline
from src.experiments.tracking import (
    complete_run,
    create_run_paths,
    dataframe_hash,
    fail_run,
    generate_run_id,
    library_versions,
    save_candidates,
    save_metrics,
    save_predictions,
    save_resources,
    save_stages,
    start_run,
    write_json,
)
from src.modeling.open_forecast import (
    build_open_training_frame,
    predict_next_opens,
    train_open_forecast,
)
from src.utils.logging_config import (
    clear_log_context,
    get_logger,
    setup_logging,
)
from src.utils.resource_monitor import ResourceMonitor, StageTimer

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Forecast gold open prices for the next 10 trading sessions",
    )
    parser.add_argument("--test-size", type=float, default=OPEN_FORECAST_TEST_SIZE)
    parser.add_argument("--cv-splits", type=int, default=OPEN_FORECAST_CV_SPLITS)
    parser.add_argument("--random-seed", type=int, default=OPEN_FORECAST_RANDOM_SEED)
    parser.add_argument("--log-level", default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    run_id = generate_run_id()
    paths = create_run_paths(run_id)
    setup_logging(
        level=args.log_level,
        log_file=paths.human_log,
        json_log_file=paths.json_log,
        run_id=run_id,
        command="open_forecast_10d",
    )
    started_at = datetime.now(timezone.utc)
    started_clock = time.perf_counter()
    stages: list[dict[str, object]] = []
    monitor = ResourceMonitor()
    monitor.start()
    db_started = False
    versions = library_versions()
    run_config = {
        "target_columns": list(OPEN_TARGET_COLUMNS),
        "horizon_sessions": OPEN_FORECAST_HORIZON,
        "test_size": args.test_size,
        "cv_splits": args.cv_splits,
        "random_seed": args.random_seed,
        "model_config": OPEN_FORECAST_MODEL_CONFIG,
        "forecast_date_policy": "US federal business-day estimate",
        "prediction_cutoff": "after completed gold session",
    }

    logger.info(
        "Open forecast run started",
        extra={
            "stage": "run",
            "target_name": "gold_open",
            "horizon_sessions": OPEN_FORECAST_HORIZON,
            "artifact_dir": str(paths.directory),
        },
    )

    try:
        with StageTimer("prepare_schema", stages):
            run_schema_pipeline(SQL_DIR)

        start_run(
            {
                "run_id": run_id,
                "experiment_name": (
                    f"gold_open_multioutput_10_session_{started_at:%Y%m%d}"
                ),
                "run_type": "train_evaluate_predict",
                "started_at": started_at,
                "target_name": "gold_open",
                "horizon_sessions": OPEN_FORECAST_HORIZON,
                "random_seed": args.random_seed,
                "artifact_dir": str(paths.directory),
                "log_path": str(paths.human_log),
                "json_log_path": str(paths.json_log),
                "config": run_config,
                "library_versions": versions,
            }
        )
        db_started = True

        with StageTimer("load_training_data", stages):
            frame = build_open_training_frame()
            data_hash = dataframe_hash(frame)
            as_of_date = frame.index.max().date()
            target_complete = frame.dropna(subset=list(OPEN_TARGET_COLUMNS))
            logger.info(
                "Training data loaded",
                extra={
                    "stage": "load_training_data",
                    "rows": len(frame),
                    "columns": len(frame.columns),
                    "complete_target_rows": len(target_complete),
                    "as_of_date": str(as_of_date),
                    "data_hash": data_hash,
                },
            )

        with StageTimer("train_and_evaluate", stages):
            result = train_open_forecast(
                frame=frame,
                test_size=args.test_size,
                random_seed=args.random_seed,
                cv_splits=args.cv_splits,
            )

        with StageTimer("persist_artifacts", stages):
            joblib.dump(result.production_model, paths.model)
            joblib.dump(result.holdout_model, paths.holdout_model)
            result.leaderboard.loc[
                result.leaderboard["selected"],
                "artifact_path",
            ] = str(paths.model)
            result.leaderboard.to_csv(paths.leaderboard, index=False)
            result.metrics.to_csv(paths.metrics, index=False)
            result.holdout_predictions.to_csv(
                paths.holdout_predictions,
                index=False,
            )
            write_json(
                paths.feature_list,
                {"feature_columns": result.feature_columns},
            )

            latest_model_dir = PROJECT_ROOT / "models" / "open_forecast"
            latest_model_dir.mkdir(parents=True, exist_ok=True)
            versioned_model = latest_model_dir / f"{run_id}.joblib"
            shutil.copy2(paths.model, versioned_model)
            shutil.copy2(paths.model, latest_model_dir / "latest_model.joblib")

        with StageTimer("verify_model_artifact", stages):
            reloaded_model = joblib.load(paths.model)
            latest_features = frame.sort_index().tail(1)
            expected_prediction = result.production_model.predict(
                latest_features[result.feature_columns].to_numpy()
            )
            reloaded_prediction = reloaded_model.predict(
                latest_features[result.feature_columns].to_numpy()
            )
            np.testing.assert_allclose(
                reloaded_prediction,
                expected_prediction,
                rtol=1e-10,
                atol=1e-10,
            )

        with StageTimer("generate_forecast", stages):
            predictions = predict_next_opens(reloaded_model)
            predictions.to_csv(paths.predictions, index=False)
            logger.info(
                "Open forecast generated",
                extra={
                    "stage": "generate_forecast",
                    "rows": len(predictions),
                    "as_of_date": str(predictions.iloc[0]["as_of_date"]),
                    "first_forecast_date": str(
                        predictions.iloc[0]["forecast_date"]
                    ),
                    "last_forecast_date": str(
                        predictions.iloc[-1]["forecast_date"]
                    ),
                },
            )

        database_started = time.perf_counter()
        try:
            save_candidates(run_id, result.leaderboard)
            save_metrics(run_id, result.metrics)
            save_predictions(run_id, predictions)
            database_status = "completed"
        except Exception:
            database_status = "failed"
            raise
        finally:
            stages.append(
                {
                    "stage_name": "persist_database_results",
                    "duration_seconds": time.perf_counter() - database_started,
                    "status": database_status,
                    "details": {},
                }
            )

        resource_summary = monitor.stop()
        resource_payload = resource_summary.to_dict()
        generate_stage = next(
            stage
            for stage in stages
            if stage["stage_name"] == "generate_forecast"
        )
        resource_payload["model_size_bytes"] = paths.model.stat().st_size
        resource_payload["holdout_model_size_bytes"] = (
            paths.holdout_model.stat().st_size
        )
        resource_payload["prediction_rows_per_second"] = (
            len(predictions) / float(generate_stage["duration_seconds"])
        )
        save_resources(run_id, resource_payload)
        save_stages(run_id, pd.DataFrame(stages))

        completed_at = datetime.now(timezone.utc)
        duration_seconds = time.perf_counter() - started_clock
        complete_run(
            run_id,
            {
                "completed_at": completed_at,
                "as_of_date": as_of_date,
                "selected_model": result.selected_name,
                "model_version": run_id,
                "data_hash": data_hash,
                "feature_count": len(result.feature_columns),
                "train_rows": result.train_rows,
                "validation_rows": result.validation_rows,
                "test_rows": result.test_rows,
                "duration_seconds": duration_seconds,
                "peak_rss_mb": resource_summary.peak_rss_mb,
                "average_cpu_percent": resource_summary.average_cpu_percent,
                "max_cpu_percent": resource_summary.max_cpu_percent,
                "read_bytes": resource_summary.read_bytes,
                "write_bytes": resource_summary.write_bytes,
            },
        )

        pd.DataFrame(
            [
                {
                    "metric_name": name,
                    "metric_value": value,
                }
                for name, value in resource_payload.items()
            ]
        ).to_csv(paths.resources, index=False)
        pd.DataFrame(stages).to_csv(paths.stages, index=False)
        metadata = {
            "run_id": run_id,
            "experiment_name": (
                f"gold_open_multioutput_10_session_{started_at:%Y%m%d}"
            ),
            "status": "completed",
            "started_at": started_at,
            "completed_at": completed_at,
            "duration_seconds": duration_seconds,
            "as_of_date": as_of_date,
            "selected_model": result.selected_name,
            "model_version": run_id,
            "data_hash": data_hash,
            "feature_count": len(result.feature_columns),
            "train_rows": result.train_rows,
            "validation_rows": result.validation_rows,
            "test_rows": result.test_rows,
            "config": run_config,
            "library_versions": versions,
            "resource_summary": resource_payload,
            "artifact_paths": {
                key: str(value)
                for key, value in paths.__dict__.items()
                if key not in {"run_id"}
            },
        }
        write_json(paths.metadata, metadata)

        logger.info(
            "Open forecast run completed",
            extra={
                "stage": "run",
                "selected_model": result.selected_name,
                "duration_seconds": duration_seconds,
                "artifact_dir": str(paths.directory),
            },
        )
        print(f"Run ID: {run_id}")
        print(f"Selected model: {result.selected_name}")
        print(f"Artifacts: {paths.directory}")
        print(predictions.to_string(index=False))
    except Exception as error:
        try:
            resource_summary = monitor.stop()
        except Exception:
            resource_summary = None
        failure_metadata = {
            "run_id": run_id,
            "status": "failed",
            "started_at": started_at,
            "failed_at": datetime.now(timezone.utc),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "config": run_config,
            "resource_summary": (
                resource_summary.to_dict()
                if resource_summary is not None
                else {}
            ),
        }
        write_json(paths.metadata, failure_metadata)
        if db_started:
            fail_run(run_id, error)
        logger.exception(
            "Open forecast run failed",
            extra={"stage": "run", "error_type": type(error).__name__},
        )
        raise
    finally:
        clear_log_context()


if __name__ == "__main__":
    main()
