"""Attach realized gold opens to stored forecasts when data becomes available."""

from __future__ import annotations

import sys
from pathlib import Path

import psycopg2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.storage.postgres_client import get_connection_params


def main() -> None:
    update_sql = """
        UPDATE forecasting.open_predictions prediction
        SET actual_open = actual.gold_open,
            absolute_error = ABS(actual.gold_open - prediction.predicted_open),
            percentage_error = 100.0 * ABS(
                actual.gold_open - prediction.predicted_open
            ) / NULLIF(actual.gold_open, 0),
            evaluated_at = NOW()
        FROM staging.daily_master actual
        WHERE prediction.forecast_date = actual.date
          AND actual.gold_open IS NOT NULL
          AND prediction.actual_open IS NULL
    """
    with psycopg2.connect(**get_connection_params()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(update_sql)
            updated = cursor.rowcount
            cursor.execute(
                """
                INSERT INTO forecasting.model_metrics (
                    run_id, model_name, split_name, horizon_step,
                    metric_name, metric_value, sample_count
                )
                SELECT
                    prediction.run_id,
                    run.selected_model,
                    'live',
                    prediction.forecast_step,
                    metric.metric_name,
                    metric.metric_value,
                    1
                FROM forecasting.open_predictions prediction
                JOIN forecasting.model_runs run USING (run_id)
                CROSS JOIN LATERAL (
                    VALUES
                        ('absolute_error', prediction.absolute_error),
                        ('percentage_error', prediction.percentage_error)
                ) AS metric(metric_name, metric_value)
                WHERE prediction.actual_open IS NOT NULL
                ON CONFLICT (
                    run_id, model_name, split_name, horizon_step, metric_name
                ) DO UPDATE SET
                    metric_value = EXCLUDED.metric_value,
                    sample_count = EXCLUDED.sample_count,
                    created_at = NOW()
                """
            )
            cursor.execute(
                """
                WITH aggregate_by_run AS (
                    SELECT
                        prediction.run_id,
                        run.selected_model,
                        COUNT(*)::INTEGER AS sample_count,
                        SQRT(AVG(POWER(
                            prediction.actual_open - prediction.predicted_open,
                            2
                        ))) AS rmse,
                        AVG(prediction.absolute_error) AS mae,
                        AVG(prediction.percentage_error) AS mape
                    FROM forecasting.open_predictions prediction
                    JOIN forecasting.model_runs run USING (run_id)
                    WHERE prediction.actual_open IS NOT NULL
                    GROUP BY prediction.run_id, run.selected_model
                )
                INSERT INTO forecasting.model_metrics (
                    run_id, model_name, split_name, horizon_step,
                    metric_name, metric_value, sample_count
                )
                SELECT
                    aggregate_by_run.run_id,
                    aggregate_by_run.selected_model,
                    'live',
                    0,
                    metric.metric_name,
                    metric.metric_value,
                    aggregate_by_run.sample_count
                FROM aggregate_by_run
                CROSS JOIN LATERAL (
                    VALUES
                        ('rmse', aggregate_by_run.rmse),
                        ('mae', aggregate_by_run.mae),
                        ('mape', aggregate_by_run.mape)
                ) AS metric(metric_name, metric_value)
                ON CONFLICT (
                    run_id, model_name, split_name, horizon_step, metric_name
                ) DO UPDATE SET
                    metric_value = EXCLUDED.metric_value,
                    sample_count = EXCLUDED.sample_count,
                    created_at = NOW()
                """
            )
    print(f"Reconciled prediction rows: {updated}")


if __name__ == "__main__":
    main()
