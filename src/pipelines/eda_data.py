"""
src/pipelines/eda_data.py
=========================
Data-loading and summary helpers for the EDA pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from config.settings import TARGET_COLUMN, TARGET_LABEL_COLUMNS
from src.data.storage.postgres_client import get_engine


@dataclass(frozen=True)
class EDADataBundle:
    """Container for the tables used in EDA."""

    master_features: pd.DataFrame
    target_labels: pd.DataFrame
    analysis_frame: pd.DataFrame
    combined: pd.DataFrame
    missing_values: pd.DataFrame


def load_master_features(limit: int | None = None) -> pd.DataFrame:
    """Load features.master_features ordered by date.

    Args:
        limit: Maximum number of rows to return. None returns all.

    Returns:
        pd.DataFrame indexed by 'date' with all master feature columns.
    """
    engine = get_engine()
    limit_clause = f"LIMIT {limit}" if limit is not None else ""
    query = f"""
        SELECT *
        FROM features.master_features
        ORDER BY date
        {limit_clause}
    """
    with engine.connect() as connection:
        return pd.read_sql(query, connection, index_col="date", parse_dates=["date"])


def load_target_labels(
    limit: int | None = None,
    target_col: str = TARGET_COLUMN,
) -> pd.DataFrame:
    """Load features.target_labels ordered by date.

    Only rows with a known value for ``target_col`` are included.

    Args:
        limit: Maximum number of rows to return. None returns all.
        target_col: Target used to filter unavailable future labels.

    Returns:
        pd.DataFrame indexed by 'date' with target label columns.
    """
    if target_col not in TARGET_LABEL_COLUMNS:
        raise ValueError(f"Unsupported target column: {target_col!r}")

    engine = get_engine()
    limit_clause = f"LIMIT {limit}" if limit is not None else ""
    query = f"""
        SELECT *
        FROM features.target_labels
        WHERE {target_col} IS NOT NULL
        ORDER BY date
        {limit_clause}
    """
    with engine.connect() as connection:
        return pd.read_sql(query, connection, index_col="date", parse_dates=["date"])


def load_current_gold_close(limit: int | None = None) -> pd.DataFrame:
    """Load current gold close as a compatibility fallback for older schemas."""

    engine = get_engine()
    limit_clause = f"LIMIT {limit}" if limit is not None else ""
    query = f"""
        SELECT date, gold_close
        FROM staging.daily_master
        WHERE gold_close IS NOT NULL
        ORDER BY date
        {limit_clause}
    """
    with engine.connect() as connection:
        return pd.read_sql(
            query,
            connection,
            index_col="date",
            parse_dates=["date"],
        )


def combine_with_targets(master_features: pd.DataFrame, target_labels: pd.DataFrame) -> pd.DataFrame:
    """Join master features and target labels on date.

    Args:
        master_features: Feature DataFrame indexed by date.
        target_labels: Target label DataFrame indexed by date.

    Returns:
        Inner-joined DataFrame containing both features and targets.
    """
    target_columns = [
        column
        for column in target_labels.columns
        if column in TARGET_LABEL_COLUMNS
    ]
    return master_features.join(target_labels[target_columns], how="inner")


def summarize_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Return missing count and percentage per column.

    Args:
        df: DataFrame to analyse.

    Returns:
        pd.DataFrame with columns 'missing_count' and 'missing_pct',
        filtered to columns that have at least one missing value.
    """
    missing = df.isna().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    summary = pd.DataFrame({"missing_count": missing, "missing_pct": missing_pct})
    summary = summary[summary["missing_count"] > 0].sort_values("missing_pct", ascending=False)
    return summary


def build_eda_bundle() -> EDADataBundle:
    """Load the EDA tables and derived summaries.

    Returns:
        EDADataBundle with master_features, target_labels, combined frame,
        and a missing-values summary.
    """
    master_features = load_master_features()
    target_labels = load_target_labels()
    if "gold_close" in master_features.columns:
        analysis_frame = master_features
    else:
        current_gold = load_current_gold_close()
        analysis_frame = master_features.join(current_gold, how="left")
    combined = combine_with_targets(analysis_frame, target_labels)
    missing_values = summarize_missing_values(master_features)
    return EDADataBundle(
        master_features=master_features,
        target_labels=target_labels,
        analysis_frame=analysis_frame,
        combined=combined,
        missing_values=missing_values,
    )


__all__ = [
    "EDADataBundle",
    "build_eda_bundle",
    "combine_with_targets",
    "load_current_gold_close",
    "load_master_features",
    "load_target_labels",
    "summarize_missing_values",
]
