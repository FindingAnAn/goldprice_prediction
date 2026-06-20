"""
src/pipelines/eda.py
====================
High-level EDA pipeline for the Gold Time Prediction project.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.pipelines.eda_data import EDADataBundle, build_eda_bundle
from src.pipelines.eda_plots import (
    plot_bollinger_bands,
    plot_correlation_heatmap,
    plot_gold_price_trend,
    plot_gold_ratios,
    plot_macro_factors_vs_gold,
    plot_return_distributions,
    plot_rsi_and_macd,
    print_target_label_statistics,
    setup_plot_style,
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class EDAReport:
    """Structured result of the EDA pipeline."""

    data: EDADataBundle

    @property
    def master_shape(self) -> tuple[int, int]:
        return self.data.master_features.shape

    @property
    def target_shape(self) -> tuple[int, int]:
        return self.data.target_labels.shape


def render_eda_report(report: EDAReport) -> None:
    """Print the main EDA summary blocks."""
    master = report.data.master_features
    combined = report.data.combined
    missing = report.data.missing_values

    print(f"[INFO] master_features shape: {master.shape}")
    if not master.empty:
        print(f"[INFO] Date range: {master.index.min().date()} -> {master.index.max().date()}")
        print(master.head(3).to_string())

    print(f"[INFO] Columns with missing values: {len(missing)}")
    if not missing.empty:
        print(missing.head(20).to_string())

    if not combined.empty:
        print(f"[INFO] Combined EDA frame shape: {combined.shape}")

    print_target_label_statistics(report.data.target_labels)


def run_eda_pipeline(show_plots: bool = True) -> EDAReport:
    """Load EDA data, print summaries, and optionally render plots."""
    logger.info("Starting EDA pipeline", extra={"show_plots": show_plots})
    setup_plot_style()
    data = build_eda_bundle()
    report = EDAReport(data=data)
    render_eda_report(report)

    if show_plots:
        plot_gold_price_trend(data.analysis_frame, show=True)
        plot_bollinger_bands(data.analysis_frame, show=True)
        plot_rsi_and_macd(data.analysis_frame, show=True)
        plot_macro_factors_vs_gold(data.analysis_frame, show=True)
        plot_gold_ratios(data.analysis_frame, show=True)
        plot_correlation_heatmap(data.combined, show=True)
        plot_return_distributions(data.analysis_frame, show=True)

    return report


__all__ = [
    "EDAReport",
    "render_eda_report",
    "run_eda_pipeline",
]
