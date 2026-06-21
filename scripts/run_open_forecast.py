"""Refresh data, benchmark hybrid models, and forecast ten gold opens."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys
import time

import joblib
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import (
    DATA_START_DATE,
    DEEP_FORECAST_DEFAULT_MAX_STEPS,
    DEEP_FORECAST_DEFAULT_WINDOWS,
    DEEP_FORECAST_MODELS,
    DEEP_FORECAST_VALIDATION_SIZE,
    OPEN_FORECAST_HORIZON,
    OPEN_FORECAST_MODEL_CONFIG,
    OPEN_FORECAST_RANDOM_SEED,
    OPEN_TARGET_COLUMNS,
    TABULAR_FORECAST_MODELS,
    TABULAR_FORECAST_TRAINING_WINDOW,
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
from src.modeling.forecast_explanations import add_forecast_context
from src.modeling.open_forecast import (
    build_sequence_forecast_frame,
    next_estimated_session_dates,
)
from src.modeling.sequence_forecast import benchmark_sequence_models
from src.modeling.tabular_forecast import (
    DirectForecastEnsemble,
    DirectForecastModel,
    benchmark_tabular_models,
    predict_direct_model,
)
from src.pipelines.eda_data import load_master_features
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
        description=(
            "Forecast gold open prices with sequence and direct tabular models"
        ),
    )
    parser.add_argument(
        "--windows",
        "--deep-windows",
        dest="windows",
        type=int,
        default=DEEP_FORECAST_DEFAULT_WINDOWS,
    )
    parser.add_argument(
        "--max-steps",
        "--deep-max-steps",
        dest="max_steps",
        type=int,
        default=DEEP_FORECAST_DEFAULT_MAX_STEPS,
    )
    parser.add_argument("--log-level", default=None)
    return parser


def _combine_predictions(
    sequence_result: object,
    tabular_result: object,
    as_of_date: object,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    sequence_rolling = sequence_result.rolling_predictions.copy()
    tabular_rolling = tabular_result.rolling_predictions.copy()
    merge_keys = [
        "unique_id",
        "cutoff_date",
        "forecast_date",
        "step",
    ]
    tabular_model_columns = [
        column
        for column in tabular_rolling.columns
        if column
        not in {
            "unique_id",
            "ds",
            "cutoff",
            "cutoff_date",
            "forecast_date",
            "step",
            "current_price",
            "actual_price",
        }
    ]
    rolling = sequence_rolling.merge(
        tabular_rolling[merge_keys + tabular_model_columns],
        on=merge_keys,
        how="inner",
        validate="one_to_one",
    )
    expected_rows = len(sequence_rolling)
    if len(rolling) != expected_rows:
        raise ValueError(
            "Sequence and tabular rolling windows do not align: "
            f"{len(rolling)} of {expected_rows} rows matched"
        )

    sequence_future = sequence_result.future_predictions.copy()
    sequence_future["forecast_date"] = next_estimated_session_dates(
        as_of_date,
        periods=OPEN_FORECAST_HORIZON,
    )
    tabular_future = tabular_result.future_predictions.copy()
    tabular_future_columns = [
        column
        for column in tabular_future.columns
        if column
        not in {
            "unique_id",
            "ds",
            "step",
            "forecast_date",
            "as_of_date",
        }
    ]
    future = sequence_future.merge(
        tabular_future[
            ["unique_id", "step", "forecast_date", *tabular_future_columns]
        ],
        on=["unique_id", "step", "forecast_date"],
        how="inner",
        validate="one_to_one",
    )
    future["as_of_date"] = pd.Timestamp(as_of_date)
    return rolling, future


def _candidate_and_metric_frames(
    sequence_result: object,
    tabular_result: object,
    paths: object,
    windows: int,
    max_steps: int,
) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    all_metrics = pd.concat(
        [sequence_result.metrics, tabular_result.metrics],
        ignore_index=True,
    )
    candidate_rows: list[dict[str, object]] = []
    metric_rows: list[dict[str, object]] = []

    for model_name, group in all_metrics.groupby("model"):
        is_sequence = model_name in DEEP_FORECAST_MODELS
        is_direct = model_name in TABULAR_FORECAST_MODELS
        if is_sequence:
            family = "deep_sequence"
            training_seconds = sequence_result.training_seconds[model_name]
            uses_exogenous = model_name in {"TiDE", "NHITS"}
            model_exogenous = (
                list(sequence_result.used_exogenous_features)
                if uses_exogenous
                else []
            )
            feature_count = 1 + len(model_exogenous)
            parameters = {
                "model_family": family,
                "evaluation_protocol": "rolling_fixed_model",
                "windows": windows,
                "max_steps": max_steps,
                "input_window_sessions": 252,
                "sequence_rows": sequence_result.sequence_rows,
                "feature_count": feature_count,
                "used_exogenous_features": model_exogenous,
                "excluded_exogenous_features": list(
                    sequence_result.excluded_exogenous_features
                ),
            }
        else:
            family = (
                "direct_tabular"
                if is_direct
                else "fixed_weight_direct_ensemble"
            )
            training_seconds = tabular_result.training_seconds[model_name]
            parameters = {
                "model_family": family,
                "evaluation_protocol": "rolling_refit_each_origin",
                "target_transform": (
                    "log(future_open/current_close)"
                ),
                "windows": windows,
                "training_window_sessions": (
                    TABULAR_FORECAST_TRAINING_WINDOW
                ),
                "feature_count": len(tabular_result.feature_columns),
                "direct_multi_horizon": True,
            }

        candidate_rows.append(
            {
                "model": model_name,
                "selected": False,
                "parameters": parameters,
                "cv_rmse": float(group["rmse"].mean()),
                "cv_mae": float(group["mae"].mean()),
                "cv_mape": float(group["mape"].mean()),
                "cv_smape": float(group["smape"].mean()),
                "cv_nrmse_mean_pct": float(
                    group["nrmse_mean_pct"].mean()
                ),
                "cv_direction_accuracy": float(
                    group["direction_accuracy"].mean()
                ),
                "training_seconds": training_seconds,
                "artifact_path": str(paths.model_directory / model_name),
            }
        )
        for row in group.itertuples(index=False):
            for metric_name in (
                "rmse",
                "mae",
                "mape",
                "smape",
                "nrmse_mean_pct",
                "direction_accuracy",
            ):
                metric_rows.append(
                    {
                        "model_name": model_name,
                        "split_name": "rolling_cv",
                        "horizon_step": int(row.horizon),
                        "metric_name": metric_name,
                        "metric_value": getattr(row, metric_name),
                        "sample_count": int(row.windows),
                    }
                )

    leaderboard = pd.DataFrame(candidate_rows).sort_values(
        ["cv_rmse", "cv_mae"],
    )
    selected_name = str(leaderboard.iloc[0]["model"])
    leaderboard.loc[
        leaderboard["model"] == selected_name,
        "selected",
    ] = True
    return leaderboard, pd.DataFrame(metric_rows), selected_name


def _persist_models(
    sequence_result: object,
    tabular_result: object,
    paths: object,
) -> None:
    for model_name, forecaster in sequence_result.fitted_forecasters.items():
        forecaster.save(
            path=str(paths.model_directory / model_name),
            save_dataset=True,
            overwrite=True,
        )
    for model_name, model in tabular_result.fitted_models.items():
        model_path = paths.model_directory / model_name
        model_path.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, model_path / "model.joblib")


def _verify_models(
    sequence_result: object,
    tabular_result: object,
    future_predictions: pd.DataFrame,
    frame: pd.DataFrame,
    paths: object,
) -> None:
    from neuralforecast import NeuralForecast

    for model_name in DEEP_FORECAST_MODELS:
        reloaded = NeuralForecast.load(
            str(paths.model_directory / model_name),
        )
        prediction = reloaded.predict().reset_index()
        np.testing.assert_allclose(
            np.exp(prediction[model_name].to_numpy()),
            future_predictions[model_name].to_numpy(),
            rtol=1e-5,
            atol=1e-5,
        )

    for model_name in TABULAR_FORECAST_MODELS:
        reloaded = joblib.load(
            paths.model_directory / model_name / "model.joblib"
        )
        prediction = predict_direct_model(reloaded, frame)
        np.testing.assert_allclose(
            prediction[model_name].to_numpy(),
            future_predictions[model_name].to_numpy(),
            rtol=1e-8,
            atol=1e-8,
        )

    for model_name, model in tabular_result.fitted_models.items():
        if not isinstance(model, DirectForecastEnsemble):
            continue
        reloaded = joblib.load(
            paths.model_directory / model_name / "model.joblib"
        )
        if reloaded != model:
            raise ValueError(f"Failed to verify ensemble artifact: {model_name}")
        expected = sum(
            weight * future_predictions[component].to_numpy()
            for weight, component in zip(
                model.weights,
                model.component_models,
            )
        )
        np.testing.assert_allclose(
            expected,
            future_predictions[model_name].to_numpy(),
            rtol=1e-12,
            atol=1e-12,
        )


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
        "random_seed": OPEN_FORECAST_RANDOM_SEED,
        "model_config": OPEN_FORECAST_MODEL_CONFIG,
        "forecast_date_policy": "US federal business-day estimate",
        "prediction_cutoff": "after completed gold session",
        "artifact_language": "English",
        "data_refresh": {
            "mode": "truncate_raw_staging_features_then_reingest",
            "start": DATA_START_DATE,
            "end": "latest_completed_session",
            "forecasting_schema_preserved": True,
        },
        "benchmark": {
            "sequence_models": list(DEEP_FORECAST_MODELS),
            "tabular_models": list(TABULAR_FORECAST_MODELS),
            "rolling_windows": args.windows,
            "deep_max_steps": args.max_steps,
            "tabular_training_window_sessions": (
                TABULAR_FORECAST_TRAINING_WINDOW
            ),
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
                    f"gold_open_hybrid_10_session_{started_at:%Y%m%d}"
                ),
                "run_type": "train_evaluate_predict",
                "started_at": started_at,
                "target_name": "gold_open",
                "horizon_sessions": OPEN_FORECAST_HORIZON,
                "random_seed": OPEN_FORECAST_RANDOM_SEED,
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
            frame = load_master_features()
            data_hash = dataframe_hash(frame)
            as_of_date = frame.index.max().date()
            logger.info(
                "Training data loaded",
                extra={
                    "stage": "load_training_data",
                    "rows": len(frame),
                    "columns": len(frame.columns),
                    "as_of_date": str(as_of_date),
                    "data_hash": data_hash,
                },
            )

        with StageTimer("train_sequence_models", stages):
            sequence_result = benchmark_sequence_models(
                n_windows=args.windows,
                max_steps=args.max_steps,
                master_features=frame,
            )

        with StageTimer("train_tabular_models", stages):
            tabular_result = benchmark_tabular_models(
                n_windows=args.windows,
                master_features=frame,
            )

        with StageTimer("select_model", stages):
            rolling_predictions, future_predictions = _combine_predictions(
                sequence_result,
                tabular_result,
                as_of_date,
            )
            leaderboard, metrics, selected_name = (
                _candidate_and_metric_frames(
                    sequence_result,
                    tabular_result,
                    paths,
                    args.windows,
                    args.max_steps,
                )
            )

        with StageTimer("persist_artifacts", stages):
            _persist_models(sequence_result, tabular_result, paths)
            leaderboard.to_csv(paths.leaderboard, index=False)
            metrics.to_csv(paths.metrics, index=False)
            pd.concat(
                [sequence_result.metrics, tabular_result.metrics],
                ignore_index=True,
            ).to_csv(paths.benchmark_metrics, index=False)
            rolling_predictions.to_csv(
                paths.rolling_predictions,
                index=False,
            )
            future_predictions.to_csv(
                paths.future_predictions,
                index=False,
            )
            tabular_result.feature_importance.to_csv(
                paths.feature_importance,
                index=False,
            )
            write_json(
                paths.feature_list,
                {
                    "sequence_target": "gold_open",
                    "sequence_exogenous_features": list(
                        sequence_result.used_exogenous_features
                    ),
                    "excluded_sequence_exogenous_features": list(
                        sequence_result.excluded_exogenous_features
                    ),
                    "tabular_target_transform": (
                        "log(future_open/current_close)"
                    ),
                    "tabular_feature_columns": list(
                        tabular_result.feature_columns
                    ),
                    "tabular_training_window_sessions": (
                        TABULAR_FORECAST_TRAINING_WINDOW
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
            write_json(
                latest_model_dir / "latest.json",
                {
                    "run_id": run_id,
                    "selected_model": selected_name,
                    "artifact_path": str(
                        paths.model_directory / selected_name
                    ),
                    "as_of_date": as_of_date,
                },
            )

        with StageTimer("verify_model_artifacts", stages):
            _verify_models(
                sequence_result,
                tabular_result,
                future_predictions,
                frame,
                paths,
            )

        with StageTimer("generate_forecast", stages):
            predictions = build_sequence_forecast_frame(
                selected_model=selected_name,
                future_predictions=future_predictions,
                rolling_predictions=rolling_predictions,
                as_of_date=as_of_date,
            )
            predictions = add_forecast_context(predictions, frame)
            predictions.to_csv(paths.predictions, index=False)
            logger.info(
                "Open forecast generated",
                extra={
                    "stage": "generate_forecast",
                    "rows": len(predictions),
                    "as_of_date": str(as_of_date),
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
                    "duration_seconds": time.perf_counter()
                    - database_started,
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
        resource_payload["model_artifact_size_bytes"] = sum(
            file.stat().st_size
            for file in paths.model_directory.rglob("*")
            if file.is_file()
        )
        resource_payload["prediction_rows_per_second"] = (
            len(predictions) / float(generate_stage["duration_seconds"])
        )
        save_resources(run_id, resource_payload)
        save_stages(run_id, pd.DataFrame(stages))

        completed_at = datetime.now(timezone.utc)
        duration_seconds = time.perf_counter() - started_clock
        selected_is_sequence = selected_name in DEEP_FORECAST_MODELS
        selected_uses_exogenous = selected_name in {"TiDE", "NHITS"}
        feature_count = (
            1
            + (
                len(sequence_result.used_exogenous_features)
                if selected_uses_exogenous
                else 0
            )
            if selected_is_sequence
            else len(tabular_result.feature_columns)
        )
        train_rows = (
            sequence_result.sequence_rows
            if selected_is_sequence
            else tabular_result.training_rows
        )
        test_rows = args.windows * OPEN_FORECAST_HORIZON
        completion_record = {
            "completed_at": completed_at,
            "as_of_date": as_of_date,
            "selected_model": selected_name,
            "model_version": run_id,
            "data_hash": data_hash,
            "feature_count": feature_count,
            "train_rows": train_rows,
            "validation_rows": DEEP_FORECAST_VALIDATION_SIZE,
            "test_rows": test_rows,
            "duration_seconds": duration_seconds,
            "peak_rss_mb": resource_summary.peak_rss_mb,
            "average_cpu_percent": resource_summary.average_cpu_percent,
            "max_cpu_percent": resource_summary.max_cpu_percent,
            "read_bytes": resource_summary.read_bytes,
            "write_bytes": resource_summary.write_bytes,
        }
        complete_run(run_id, completion_record)

        pd.DataFrame(
            [
                {"metric_name": name, "metric_value": value}
                for name, value in resource_payload.items()
            ]
        ).to_csv(paths.resources, index=False)
        pd.DataFrame(stages).to_csv(paths.stages, index=False)
        write_json(
            paths.metadata,
            {
                "run_id": run_id,
                "experiment_name": (
                    f"gold_open_hybrid_10_session_{started_at:%Y%m%d}"
                ),
                "status": "completed",
                "started_at": started_at,
                **completion_record,
                "config": run_config,
                "library_versions": versions,
                "resource_summary": resource_payload,
                "artifact_paths": {
                    key: str(value)
                    for key, value in paths.__dict__.items()
                    if key != "run_id"
                },
            },
        )

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
        write_json(
            paths.metadata,
            {
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
            },
        )
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
