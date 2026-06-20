"""Train, evaluate and persist the next-10-session gold open forecast."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
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
    DEEP_FORECAST_DEFAULT_MAX_STEPS,
    DEEP_FORECAST_DEFAULT_WINDOWS,
    DEEP_FORECAST_MODELS,
    OPEN_FORECAST_CV_SPLITS,
    OPEN_FORECAST_HORIZON,
    OPEN_FORECAST_MODEL_CONFIG,
    OPEN_FORECAST_RANDOM_SEED,
    OPEN_FORECAST_TEST_SIZE,
    OPEN_TARGET_COLUMNS,
    DATA_START_DATE,
)
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
    next_estimated_session_dates,
    predict_next_opens,
    train_open_forecast,
)
from src.modeling.forecast_explanations import add_forecast_context
from src.modeling.sequence_forecast import benchmark_sequence_models
from src.pipelines.ingestion import (
    prepare_database_schema,
    run_ingestion_pipeline,
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
    parser.add_argument(
        "--deep-windows",
        type=int,
        default=DEEP_FORECAST_DEFAULT_WINDOWS,
    )
    parser.add_argument(
        "--deep-max-steps",
        type=int,
        default=DEEP_FORECAST_DEFAULT_MAX_STEPS,
    )
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
        "data_refresh": {
            "mode": "truncate_raw_staging_features_then_reingest",
            "start": DATA_START_DATE,
            "end": "latest_completed_session",
            "forecasting_schema_preserved": True,
        },
        "mandatory_deep_models": {
            "models": list(DEEP_FORECAST_MODELS),
            "rolling_windows": args.deep_windows,
            "max_steps": args.deep_max_steps,
        },
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
        with StageTimer("prepare_database_schema", stages):
            prepare_database_schema()
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

        with StageTimer("full_refresh_ingestion", stages):
            run_ingestion_pipeline(
                start=DATA_START_DATE,
                end=None,
                prepare_schema=False,
                full_refresh=True,
                validate=True,
            )

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

        with StageTimer("train_mandatory_deep_models", stages):
            sequence_result = benchmark_sequence_models(
                n_windows=args.deep_windows,
                max_steps=args.deep_max_steps,
                master_features=frame,
            )
            deep_metrics = sequence_result.metrics
            deep_predictions = sequence_result.rolling_predictions
            deep_future_predictions = sequence_result.future_predictions
            future_dates = next_estimated_session_dates(
                as_of_date,
                periods=OPEN_FORECAST_HORIZON,
            )
            deep_future_predictions["forecast_date"] = future_dates.date
            deep_future_predictions["forecast_step"] = np.arange(
                1,
                OPEN_FORECAST_HORIZON + 1,
            )
            deep_candidate_rows: list[dict[str, object]] = []
            deep_metric_rows: list[dict[str, object]] = []
            for model_name, group in deep_metrics.groupby("model"):
                deep_candidate_rows.append(
                    {
                        "model": f"deep_{model_name}",
                        "selected": False,
                        "parameters": {
                            "model_family": "deep_sequence",
                            "evaluation_protocol": "rolling_fixed_model",
                            "mandatory": True,
                            "windows": args.deep_windows,
                            "max_steps": args.deep_max_steps,
                            "sequence_rows": sequence_result.sequence_rows,
                            "used_exogenous_features": list(
                                sequence_result.used_exogenous_features
                            ),
                            "excluded_exogenous_features": list(
                                sequence_result.excluded_exogenous_features
                            ),
                        },
                        "cv_rmse": float(group["rmse"].mean()),
                        "holdout_rmse": None,
                        "holdout_mae": None,
                        "holdout_mape": None,
                        "holdout_r2": None,
                        "rmse_improvement_vs_persistence_pct": float(
                            group[
                                "rmse_improvement_vs_persistence_pct"
                            ].mean()
                        ),
                        "training_seconds": sequence_result.training_seconds[
                            model_name
                        ],
                        "artifact_path": str(
                            paths.deep_model_directory / model_name
                        ),
                    }
                )
                for row in group.itertuples(index=False):
                    for metric_name in (
                        "rmse",
                        "mae",
                        "mape",
                        "direction_accuracy",
                        "persistence_rmse",
                        "rmse_improvement_vs_persistence_pct",
                    ):
                        deep_metric_rows.append(
                            {
                                "model_name": f"deep_{model_name}",
                                "split_name": "rolling_cv",
                                "horizon_step": int(row.horizon),
                                "metric_name": metric_name,
                                "metric_value": getattr(row, metric_name),
                                "sample_count": int(row.windows),
                            }
                        )
            persistence_rolling_rmse = float(
                deep_metrics[
                    ["horizon", "persistence_rmse"]
                ]
                .drop_duplicates("horizon")["persistence_rmse"]
                .mean()
            )
            baseline_leaderboard = result.leaderboard.copy()
            baseline_leaderboard["cv_rmse"] = persistence_rolling_rmse
            baseline_leaderboard[
                "rmse_improvement_vs_persistence_pct"
            ] = 0.0
            leaderboard = pd.concat(
                [
                    baseline_leaderboard,
                    pd.DataFrame(deep_candidate_rows),
                ],
                ignore_index=True,
            )
            leaderboard["selected"] = False
            selected_name = str(
                leaderboard.sort_values("cv_rmse").iloc[0]["model"]
            )
            leaderboard.loc[
                leaderboard["model"] == selected_name,
                "selected",
            ] = True
            metrics = pd.concat(
                [
                    result.metrics,
                    pd.DataFrame(deep_metric_rows),
                ],
                ignore_index=True,
            )

        with StageTimer("persist_artifacts", stages):
            joblib.dump(result.production_model, paths.model)
            joblib.dump(result.holdout_model, paths.holdout_model)
            for model_name, forecaster in (
                sequence_result.fitted_forecasters.items()
            ):
                forecaster.save(
                    path=str(paths.deep_model_directory / model_name),
                    save_dataset=True,
                    overwrite=True,
                )
            leaderboard.loc[
                (leaderboard["selected"])
                & (leaderboard["model"] == "persistence_close"),
                "artifact_path",
            ] = str(paths.model)
            leaderboard.to_csv(paths.leaderboard, index=False)
            metrics.to_csv(paths.metrics, index=False)
            deep_metrics.to_csv(paths.deep_model_metrics, index=False)
            deep_predictions.to_csv(
                paths.deep_model_predictions,
                index=False,
            )
            deep_future_predictions.to_csv(
                paths.deep_model_future_predictions,
                index=False,
            )
            result.holdout_predictions.to_csv(
                paths.holdout_predictions,
                index=False,
            )
            write_json(
                paths.feature_list,
                {
                    "tabular_baseline_features": result.feature_columns,
                    "sequence_exogenous_features": list(
                        sequence_result.used_exogenous_features
                    ),
                    "excluded_sequence_exogenous_features": list(
                        sequence_result.excluded_exogenous_features
                    ),
                    "sequence_rows": sequence_result.sequence_rows,
                    "sequence_start_date": (
                        sequence_result.sequence_start_date
                    ),
                    "sequence_end_date": sequence_result.sequence_end_date,
                },
            )

            latest_model_dir = PROJECT_ROOT / "models" / "open_forecast"
            latest_model_dir.mkdir(parents=True, exist_ok=True)
            versioned_model = latest_model_dir / f"{run_id}.joblib"
            shutil.copy2(paths.model, versioned_model)
            shutil.copy2(paths.model, latest_model_dir / "latest_model.joblib")
            if selected_name.startswith("deep_"):
                selected_alias = selected_name.removeprefix("deep_")
                selected_forecaster = (
                    sequence_result.fitted_forecasters[selected_alias]
                )
                selected_forecaster.save(
                    path=str(latest_model_dir / f"{run_id}_deep"),
                    save_dataset=True,
                    overwrite=True,
                )
                selected_forecaster.save(
                    path=str(latest_model_dir / "latest_deep"),
                    save_dataset=True,
                    overwrite=True,
                )

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
            from neuralforecast import NeuralForecast

            for model_name in DEEP_FORECAST_MODELS:
                reloaded_deep = NeuralForecast.load(
                    str(paths.deep_model_directory / model_name),
                )
                reloaded_deep_prediction = (
                    reloaded_deep.predict().reset_index()
                )
                np.testing.assert_allclose(
                    np.exp(reloaded_deep_prediction[model_name].to_numpy()),
                    deep_future_predictions[model_name].to_numpy(),
                    rtol=1e-5,
                    atol=1e-5,
                )

        with StageTimer("generate_forecast", stages):
            predictions = predict_next_opens(reloaded_model)
            if selected_name.startswith("deep_"):
                deep_alias = selected_name.removeprefix("deep_")
                predictions["predicted_open"] = deep_future_predictions[
                    deep_alias
                ].to_numpy()
                residuals = deep_predictions.assign(
                    absolute_residual=lambda data: np.abs(
                        data["actual_price"] - data[deep_alias]
                    )
                )
                interval_80 = (
                    residuals.groupby("step")["absolute_residual"]
                    .quantile(0.80)
                    .reindex(range(1, OPEN_FORECAST_HORIZON + 1))
                    .to_numpy()
                )
                interval_95 = (
                    residuals.groupby("step")["absolute_residual"]
                    .quantile(0.95)
                    .reindex(range(1, OPEN_FORECAST_HORIZON + 1))
                    .to_numpy()
                )
                predictions["lower_80"] = (
                    predictions["predicted_open"] - interval_80
                )
                predictions["upper_80"] = (
                    predictions["predicted_open"] + interval_80
                )
                predictions["lower_95"] = (
                    predictions["predicted_open"] - interval_95
                )
                predictions["upper_95"] = (
                    predictions["predicted_open"] + interval_95
                )
            predictions = add_forecast_context(predictions, frame)
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
                    "selected_model": selected_name,
                },
            )

        database_started = time.perf_counter()
        try:
            save_candidates(run_id, leaderboard)
            save_metrics(run_id, metrics)
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
        resource_payload["deep_model_size_bytes"] = sum(
            file.stat().st_size
            for file in paths.deep_model_directory.rglob("*")
            if file.is_file()
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
                "selected_model": selected_name,
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
            "selected_model": selected_name,
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
                "selected_model": selected_name,
                "duration_seconds": duration_seconds,
                "artifact_dir": str(paths.directory),
            },
        )
        print(f"Run ID: {run_id}")
        print(f"Selected model: {selected_name}")
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
