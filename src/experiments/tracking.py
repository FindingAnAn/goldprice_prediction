"""Filesystem and PostgreSQL experiment tracking helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import platform
from typing import Any
from uuid import uuid4

import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import Json, execute_values

from config.settings import PREDICTIONS_DIR
from src.data.storage.postgres_client import get_connection_params


@dataclass(frozen=True)
class RunPaths:
    run_id: str
    directory: Path
    human_log: Path
    json_log: Path
    metadata: Path
    leaderboard: Path
    metrics: Path
    predictions: Path
    resources: Path
    stages: Path
    feature_list: Path
    holdout_predictions: Path
    deep_model_metrics: Path
    deep_model_predictions: Path
    deep_model_future_predictions: Path
    deep_model_directory: Path
    model: Path
    holdout_model: Path


def generate_run_id(prefix: str = "gold_open_10d") -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}_{timestamp}_{uuid4().hex[:8]}"


def create_run_paths(
    run_id: str,
    root: Path = PREDICTIONS_DIR / "open_10d",
) -> RunPaths:
    directory = root / run_id
    directory.mkdir(parents=True, exist_ok=False)
    return RunPaths(
        run_id=run_id,
        directory=directory,
        human_log=directory / "run.log",
        json_log=directory / "run.jsonl",
        metadata=directory / "metadata.json",
        leaderboard=directory / "leaderboard.csv",
        metrics=directory / "metrics.csv",
        predictions=directory / "open_predictions.csv",
        resources=directory / "resource_metrics.csv",
        stages=directory / "stage_metrics.csv",
        feature_list=directory / "feature_columns.json",
        holdout_predictions=directory / "holdout_predictions.csv",
        deep_model_metrics=directory / "deep_model_metrics.csv",
        deep_model_predictions=directory / "deep_model_predictions.csv",
        deep_model_future_predictions=(
            directory / "deep_model_future_predictions.csv"
        ),
        deep_model_directory=directory / "deep_models",
        model=directory / "model.joblib",
        holdout_model=directory / "model_holdout.joblib",
    )


def dataframe_hash(frame: pd.DataFrame) -> str:
    hashes = pd.util.hash_pandas_object(frame, index=True).to_numpy(
        dtype=np.uint64,
    )
    return hashlib.sha256(hashes.tobytes()).hexdigest()


def library_versions() -> dict[str, str]:
    packages = (
        "pandas",
        "numpy",
        "scikit-learn",
        "joblib",
        "sqlalchemy",
        "psycopg2-binary",
        "psutil",
        "neuralforecast",
        "torch",
    )
    versions = {"python": platform.python_version()}
    for package in packages:
        try:
            versions[package] = version(package)
        except PackageNotFoundError:
            continue
    return versions


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def _connect():
    return psycopg2.connect(**get_connection_params())


def start_run(record: dict[str, Any]) -> None:
    sql = """
        INSERT INTO forecasting.model_runs (
            run_id, experiment_name, run_type, status, started_at,
            target_name, horizon_sessions, random_seed, artifact_dir,
            log_path, json_log_path, config, library_versions
        ) VALUES (
            %(run_id)s, %(experiment_name)s, %(run_type)s, 'running',
            %(started_at)s, %(target_name)s, %(horizon_sessions)s,
            %(random_seed)s, %(artifact_dir)s, %(log_path)s,
            %(json_log_path)s, %(config)s, %(library_versions)s
        )
        ON CONFLICT (run_id) DO UPDATE SET
            status = 'running',
            updated_at = NOW()
    """
    params = dict(record)
    params["config"] = Json(record.get("config", {}))
    params["library_versions"] = Json(record.get("library_versions", {}))
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)


def complete_run(run_id: str, record: dict[str, Any]) -> None:
    sql = """
        UPDATE forecasting.model_runs
        SET status = 'completed',
            completed_at = %(completed_at)s,
            as_of_date = %(as_of_date)s,
            selected_model = %(selected_model)s,
            model_version = %(model_version)s,
            data_hash = %(data_hash)s,
            feature_count = %(feature_count)s,
            train_rows = %(train_rows)s,
            validation_rows = %(validation_rows)s,
            test_rows = %(test_rows)s,
            duration_seconds = %(duration_seconds)s,
            peak_rss_mb = %(peak_rss_mb)s,
            average_cpu_percent = %(average_cpu_percent)s,
            max_cpu_percent = %(max_cpu_percent)s,
            read_bytes = %(read_bytes)s,
            write_bytes = %(write_bytes)s,
            updated_at = NOW()
        WHERE run_id = %(run_id)s
    """
    params = {"run_id": run_id, **record}
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)


def fail_run(run_id: str, error: BaseException) -> None:
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE forecasting.model_runs
                SET status = 'failed',
                    completed_at = NOW(),
                    error_type = %s,
                    error_message = %s,
                    updated_at = NOW()
                WHERE run_id = %s
                """,
                (type(error).__name__, str(error)[:4000], run_id),
            )


def save_candidates(run_id: str, candidates: pd.DataFrame) -> None:
    def nullable_number(value: object) -> float | None:
        return None if pd.isna(value) else float(value)

    rows = [
        (
            run_id,
            row.model,
            bool(row.selected),
            Json(row.parameters if isinstance(row.parameters, dict) else {}),
            nullable_number(row.cv_rmse),
            nullable_number(row.holdout_rmse),
            nullable_number(row.holdout_mae),
            nullable_number(row.holdout_mape),
            nullable_number(row.holdout_r2),
            nullable_number(row.rmse_improvement_vs_persistence_pct),
            nullable_number(row.training_seconds),
            row.artifact_path,
        )
        for row in candidates.itertuples(index=False)
    ]
    sql = """
        INSERT INTO forecasting.model_candidates (
            run_id, model_name, selected, parameters, cv_rmse,
            holdout_rmse, holdout_mae, holdout_mape, holdout_r2,
            rmse_improvement_vs_persistence_pct,
            training_seconds, artifact_path
        ) VALUES %s
        ON CONFLICT (run_id, model_name) DO UPDATE SET
            selected = EXCLUDED.selected,
            parameters = EXCLUDED.parameters,
            cv_rmse = EXCLUDED.cv_rmse,
            holdout_rmse = EXCLUDED.holdout_rmse,
            holdout_mae = EXCLUDED.holdout_mae,
            holdout_mape = EXCLUDED.holdout_mape,
            holdout_r2 = EXCLUDED.holdout_r2,
            rmse_improvement_vs_persistence_pct =
                EXCLUDED.rmse_improvement_vs_persistence_pct,
            training_seconds = EXCLUDED.training_seconds,
            artifact_path = EXCLUDED.artifact_path
    """
    with _connect() as connection:
        with connection.cursor() as cursor:
            execute_values(cursor, sql, rows, page_size=100)


def save_metrics(run_id: str, metrics: pd.DataFrame) -> None:
    rows = [
        (
            run_id,
            row.model_name,
            row.split_name,
            int(row.horizon_step),
            row.metric_name,
            None if pd.isna(row.metric_value) else float(row.metric_value),
            int(row.sample_count),
        )
        for row in metrics.itertuples(index=False)
    ]
    sql = """
        INSERT INTO forecasting.model_metrics (
            run_id, model_name, split_name, horizon_step,
            metric_name, metric_value, sample_count
        ) VALUES %s
        ON CONFLICT (
            run_id, model_name, split_name, horizon_step, metric_name
        ) DO UPDATE SET
            metric_value = EXCLUDED.metric_value,
            sample_count = EXCLUDED.sample_count
    """
    with _connect() as connection:
        with connection.cursor() as cursor:
            execute_values(cursor, sql, rows, page_size=500)


def save_predictions(run_id: str, predictions: pd.DataFrame) -> None:
    rows = [
        (
            run_id,
            row.as_of_date,
            int(row.forecast_step),
            row.forecast_date,
            float(row.predicted_open),
            row.reference_close,
            row.predicted_change_amount,
            row.predicted_change_pct,
            row.forecast_direction,
            row.lower_80,
            row.upper_80,
            row.lower_95,
            row.upper_95,
            bool(row.is_estimated_date),
            row.top_reason_1,
            row.top_reason_2,
            row.top_reason_3,
            row.explanation_method,
        )
        for row in predictions.itertuples(index=False)
    ]
    sql = """
        INSERT INTO forecasting.open_predictions (
            run_id, as_of_date, forecast_step, forecast_date,
            predicted_open, reference_close, predicted_change_amount,
            predicted_change_pct, forecast_direction,
            lower_80, upper_80, lower_95, upper_95,
            is_estimated_date, top_reason_1, top_reason_2, top_reason_3,
            explanation_method
        ) VALUES %s
        ON CONFLICT (run_id, forecast_step) DO UPDATE SET
            forecast_date = EXCLUDED.forecast_date,
            predicted_open = EXCLUDED.predicted_open,
            reference_close = EXCLUDED.reference_close,
            predicted_change_amount = EXCLUDED.predicted_change_amount,
            predicted_change_pct = EXCLUDED.predicted_change_pct,
            forecast_direction = EXCLUDED.forecast_direction,
            lower_80 = EXCLUDED.lower_80,
            upper_80 = EXCLUDED.upper_80,
            lower_95 = EXCLUDED.lower_95,
            upper_95 = EXCLUDED.upper_95,
            is_estimated_date = EXCLUDED.is_estimated_date,
            top_reason_1 = EXCLUDED.top_reason_1,
            top_reason_2 = EXCLUDED.top_reason_2,
            top_reason_3 = EXCLUDED.top_reason_3,
            explanation_method = EXCLUDED.explanation_method
    """
    with _connect() as connection:
        with connection.cursor() as cursor:
            execute_values(cursor, sql, rows, page_size=100)


def save_stages(run_id: str, stages: pd.DataFrame) -> None:
    rows = [
        (
            run_id,
            row.stage_name,
            float(row.duration_seconds),
            row.status,
            Json(row.details if isinstance(row.details, dict) else {}),
        )
        for row in stages.itertuples(index=False)
    ]
    sql = """
        INSERT INTO forecasting.stage_metrics (
            run_id, stage_name, duration_seconds, status, details
        ) VALUES %s
        ON CONFLICT (run_id, stage_name) DO UPDATE SET
            duration_seconds = EXCLUDED.duration_seconds,
            status = EXCLUDED.status,
            details = EXCLUDED.details
    """
    with _connect() as connection:
        with connection.cursor() as cursor:
            execute_values(cursor, sql, rows, page_size=100)


def save_resources(run_id: str, resources: dict[str, float | int]) -> None:
    units = {
        "peak_rss_mb": "MB",
        "average_rss_mb": "MB",
        "average_cpu_percent": "percent",
        "max_cpu_percent": "percent",
        "aggregate_average_cpu_percent": "percent_across_cores",
        "aggregate_max_cpu_percent": "percent_across_cores",
        "logical_cpu_count": "count",
        "read_bytes": "bytes",
        "write_bytes": "bytes",
        "samples": "count",
        "model_size_bytes": "bytes",
        "holdout_model_size_bytes": "bytes",
        "deep_model_size_bytes": "bytes",
        "prediction_rows_per_second": "rows_per_second",
    }
    rows = [
        (run_id, name, float(value), units.get(name, "value"))
        for name, value in resources.items()
    ]
    sql = """
        INSERT INTO forecasting.resource_metrics (
            run_id, metric_name, metric_value, unit
        ) VALUES %s
        ON CONFLICT (run_id, metric_name) DO UPDATE SET
            metric_value = EXCLUDED.metric_value,
            unit = EXCLUDED.unit,
            recorded_at = NOW()
    """
    with _connect() as connection:
        with connection.cursor() as cursor:
            execute_values(cursor, sql, rows, page_size=100)


__all__ = [
    "RunPaths",
    "complete_run",
    "create_run_paths",
    "dataframe_hash",
    "fail_run",
    "generate_run_id",
    "library_versions",
    "save_candidates",
    "save_metrics",
    "save_predictions",
    "save_resources",
    "save_stages",
    "start_run",
    "write_json",
]
