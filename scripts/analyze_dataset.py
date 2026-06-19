"""Reproducible EDA diagnostics for the gold-price dataset."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import POINT_IN_TIME_UNSAFE_FEATURE_COLUMNS
from src.data.storage.postgres_client import get_engine
from src.modeling.train import infer_feature_columns
from src.pipelines.eda_data import (
    combine_with_targets,
    load_current_gold_close,
    load_master_features,
    load_target_labels,
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "predictions" / "eda"


def _top_spearman_correlations(
    frame: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
) -> pd.DataFrame:
    correlations = frame[feature_cols + [target_col]].corr(
        method="spearman",
        numeric_only=True,
    )[target_col].drop(target_col)
    return (
        correlations.rename("spearman")
        .to_frame()
        .assign(abs_spearman=lambda item: item["spearman"].abs())
        .sort_values("abs_spearman", ascending=False)
    )


def _high_correlation_pairs(
    frame: pd.DataFrame,
    feature_cols: list[str],
    threshold: float = 0.98,
) -> pd.DataFrame:
    corr = frame[feature_cols].corr(numeric_only=True).abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    pairs = [
        (left, right, upper.loc[left, right])
        for left in upper.index
        for right in upper.columns
        if pd.notna(upper.loc[left, right]) and upper.loc[left, right] >= threshold
    ]
    return pd.DataFrame(pairs, columns=["feature_1", "feature_2", "abs_corr"]).sort_values(
        "abs_corr",
        ascending=False,
    )


def _standardized_drift(
    frame: pd.DataFrame,
    feature_cols: list[str],
) -> pd.DataFrame:
    split = int(len(frame) * 0.8)
    reference = frame.iloc[:split][feature_cols]
    recent = frame.iloc[split:][feature_cols]
    pooled_std = reference.std().replace(0, np.nan)
    smd = ((recent.mean() - reference.mean()) / pooled_std).replace(
        [np.inf, -np.inf],
        np.nan,
    )
    return (
        smd.rename("standardized_mean_shift")
        .abs()
        .sort_values(ascending=False)
        .to_frame()
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    master = load_master_features()
    targets = load_target_labels(target_col="next_7_day_price_change")
    if "gold_close" in master.columns:
        analysis_features = master
    else:
        analysis_features = master.join(load_current_gold_close(), how="left")
    analysis = combine_with_targets(analysis_features, targets).sort_index()

    feature_cols = infer_feature_columns(
        analysis,
        target_col="next_7_day_price_change",
    )
    valid = analysis.dropna(
        subset=["gold_high", "gold_low", "gold_volume", "next_7_day_price_change"]
    )

    missing = pd.DataFrame(
        {
            "missing_count": master.isna().sum(),
            "missing_pct": master.isna().mean() * 100,
        }
    ).sort_values("missing_pct", ascending=False)
    target_summary = analysis["next_7_day_price_change"].describe(
        percentiles=[0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]
    )
    yearly_target = (
        analysis["next_7_day_price_change"]
        .groupby(analysis.index.year)
        .agg(["count", "mean", "std", "median", "min", "max"])
    )
    top_corr = _top_spearman_correlations(valid, feature_cols, "next_7_day_price_change")
    high_corr = _high_correlation_pairs(valid, feature_cols)
    drift = _standardized_drift(valid, feature_cols)

    with get_engine().connect() as connection:
        data_quality = pd.read_sql(
            text(
                """
                SELECT
                    COUNT(*) AS staging_rows,
                    COUNT(*) FILTER (WHERE gold_close IS NOT NULL) AS gold_rows,
                    COUNT(*) FILTER (WHERE is_outlier) AS outlier_rows,
                    COUNT(DISTINCT date) AS distinct_dates,
                    MIN(date) AS min_date,
                    MAX(date) AS max_date
                FROM staging.daily_master
                """
            ),
            connection,
        )

    missing.to_csv(OUTPUT_DIR / "missing_values.csv")
    top_corr.to_csv(OUTPUT_DIR / "target_spearman_correlations.csv")
    high_corr.to_csv(OUTPUT_DIR / "high_feature_correlations.csv", index=False)
    drift.to_csv(OUTPUT_DIR / "feature_drift.csv")
    yearly_target.to_csv(OUTPUT_DIR / "target_by_year.csv")

    print("=== DATA QUALITY ===")
    print(data_quality.to_string(index=False))
    print(f"master_shape={master.shape}")
    print(f"analysis_shape={analysis.shape}")
    print(f"model_eligible_shape={valid.shape}")
    print(f"date_range={analysis.index.min().date()} -> {analysis.index.max().date()}")
    print(f"point_in_time_blocked={list(POINT_IN_TIME_UNSAFE_FEATURE_COLUMNS)}")

    print("\n=== TARGET t+7 RETURN (%) ===")
    print(target_summary.to_string())

    print("\n=== TOP SPEARMAN CORRELATIONS WITH t+7 RETURN ===")
    print(top_corr.head(20).to_string())

    print("\n=== HIGHLY REDUNDANT FEATURE PAIRS (|corr| >= 0.98) ===")
    print(high_corr.head(20).to_string(index=False))

    print("\n=== LARGEST TRAIN/RECENT DISTRIBUTION SHIFTS ===")
    print(drift.head(20).to_string())

    print(f"\nSaved EDA tables to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
