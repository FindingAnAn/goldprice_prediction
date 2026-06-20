"""
src/data/storage/__init__.py
==============================
Export PostgreSQL client helpers.
"""

from .postgres_client import (
    get_engine,
    get_connection_params,
    upsert_dataframe,
    execute_sql_file,
    run_schema_pipeline,
    run_feature_pipeline,
    truncate_pipeline_data,
    table_exists,
    get_row_count,
    get_row_counts,
)

__all__ = [
    "get_engine",
    "get_connection_params",
    "upsert_dataframe",
    "execute_sql_file",
    "run_schema_pipeline",
    "run_feature_pipeline",
    "truncate_pipeline_data",
    "table_exists",
    "get_row_count",
    "get_row_counts",
]
