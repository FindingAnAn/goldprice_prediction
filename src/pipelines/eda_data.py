"""
src/pipelines/eda_data.py
=========================
Data-loading and summary helpers for the EDA pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.data.storage.postgres_client import get_engine


@dataclass(frozen=True)
class EDADataBundle:
    """Container for the tables used in EDA."""

    master_features: pd.DataFrame
    target_labels: pd.DataFrame
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


def load_target_labels(limit: int | None = None) -> pd.DataFrame:
    """Load features.target_labels ordered by date.

    Only rows where ``next_1_day_price`` is not NULL are included.

    Args:
        limit: Maximum number of rows to return. None returns all.

    Returns:
        pd.DataFrame indexed by 'date' with target label columns.
    """
    engine = get_engine()
    limit_clause = f"LIMIT {limit}" if limit is not None else ""
    query = f"""
        SELECT *
        FROM features.target_labels
        WHERE next_1_day_price IS NOT NULL
        ORDER BY date
        {limit_clause}
    """
    with engine.connect() as connection:
        return pd.read_sql(query, connection, index_col="date", parse_dates=["date"])


def combine_with_targets(master_features: pd.DataFrame, target_labels: pd.DataFrame) -> pd.DataFrame:
    """Join master features and target labels on date.

    Args:
        master_features: Feature DataFrame indexed by date.
        target_labels: Target label DataFrame indexed by date.

    Returns:
        Inner-joined DataFrame containing both features and targets.
    """
    return master_features.join(target_labels, how="inner")


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
    combined = combine_with_targets(master_features, target_labels)
    missing_values = summarize_missing_values(master_features)
    return EDADataBundle(
        master_features=master_features,
        target_labels=target_labels,
        combined=combined,
        missing_values=missing_values,
    )


__all__ = [
    "EDADataBundle",
    "build_eda_bundle",
    "combine_with_targets",
    "load_master_features",
    "load_target_labels",
    "summarize_missing_values",
]