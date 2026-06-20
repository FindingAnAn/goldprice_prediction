"""
src/pipelines/eda_plots.py
==========================
Visualization helpers for the EDA pipeline.
"""

from __future__ import annotations

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def setup_plot_style() -> None:
    """Apply a consistent plotting style for the EDA pipeline."""
    sns.set_theme(style="whitegrid")
    plt.rcParams["figure.figsize"] = (14, 5)


def _finalize(fig: plt.Figure, show: bool) -> plt.Figure:
    fig.tight_layout()
    if show:
        plt.show()
    return fig


def plot_gold_price_trend(df: pd.DataFrame, show: bool = True) -> plt.Figure:
    """Plot gold close price with optional moving averages."""
    fig, ax = plt.subplots(figsize=(16, 5))
    ax.plot(df.index, df["gold_close"], lw=1.2, color="goldenrod", label="Gold Close")

    if "sma_20" in df.columns:
        ax.plot(df.index, df["sma_20"], lw=1, color="blue", alpha=0.7, label="SMA 20")
    if "sma_200" in df.columns:
        ax.plot(df.index, df["sma_200"], lw=1, color="red", alpha=0.7, label="SMA 200")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_title("Gold Price (USD/oz) with Moving Averages", fontsize=14)
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (USD)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    return _finalize(fig, show)


def plot_bollinger_bands(df: pd.DataFrame, lookback: str = "2Y", show: bool = True) -> plt.Figure:
    """Plot gold price with Bollinger bands over a recent lookback window."""
    df_recent = df.last(lookback).copy()
    fig, ax = plt.subplots(figsize=(16, 5))
    ax.plot(df_recent.index, df_recent["gold_close"], lw=1.2, color="goldenrod", label="Gold Close")
    if "bb_upper" in df_recent.columns:
        ax.plot(df_recent.index, df_recent["bb_upper"], lw=1, color="gray", linestyle="--", label="BB Upper")
        ax.plot(df_recent.index, df_recent["bb_lower"], lw=1, color="gray", linestyle="--", label="BB Lower")
        ax.fill_between(df_recent.index, df_recent["bb_lower"], df_recent["bb_upper"], alpha=0.1, color="gray")
    ax.set_title("Bollinger Bands (Recent Window)", fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    return _finalize(fig, show)


def plot_rsi_and_macd(df: pd.DataFrame, lookback: str = "1Y", show: bool = True) -> plt.Figure:
    """Plot gold price, RSI, and MACD in stacked subplots."""
    df_recent = df.last(lookback).copy()
    fig, axes = plt.subplots(3, 1, figsize=(16, 12), sharex=True)

    axes[0].plot(df_recent.index, df_recent["gold_close"], color="goldenrod")
    axes[0].set_title("Gold Close")
    axes[0].grid(True, alpha=0.3)

    if "rsi_14" in df_recent.columns:
        axes[1].plot(df_recent.index, df_recent["rsi_14"], color="purple")
        axes[1].axhline(70, color="red", linestyle="--", alpha=0.5, label="Overbought (70)")
        axes[1].axhline(30, color="green", linestyle="--", alpha=0.5, label="Oversold (30)")
        axes[1].set_title("RSI (14)")
        axes[1].set_ylim(0, 100)
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

    if "macd" in df_recent.columns:
        axes[2].plot(df_recent.index, df_recent["macd"], color="blue", label="MACD")
        axes[2].plot(df_recent.index, df_recent["macd_signal"], color="red", label="Signal")
        if "macd_hist" in df_recent.columns:
            axes[2].bar(df_recent.index, df_recent["macd_hist"], color="gray", alpha=0.3, label="Histogram")
        axes[2].axhline(0, color="black", lw=0.5)
        axes[2].set_title("MACD (12, 26, 9)")
        axes[2].legend()
        axes[2].grid(True, alpha=0.3)

    return _finalize(fig, show)


def plot_macro_factors_vs_gold(df: pd.DataFrame, show: bool = True) -> plt.Figure:
    """Plot gold price against selected macro factors."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    macro_pairs = [
        ("dxy_close", "DXY Index", "steelblue"),
        ("us_10y_yield", "US 10Y Yield (%)", "firebrick"),
        ("real_yield", "Real Yield (%)", "darkorange"),
        ("vix", "VIX", "darkgreen"),
    ]

    for ax, (column, label, color) in zip(axes.flat, macro_pairs):
        if column in df.columns:
            secondary = ax.twinx()
            ax.plot(df.index, df["gold_close"], color="goldenrod", lw=1, alpha=0.7, label="Gold")
            secondary.plot(df.index, df[column], color=color, lw=1, alpha=0.7, label=label)
            ax.set_title(f"Gold vs {label}")
            ax.set_ylabel("Gold (USD)", color="goldenrod")
            secondary.set_ylabel(label, color=color)
            ax.grid(True, alpha=0.3)

    fig.suptitle("Macro Factors vs Gold Price", fontsize=14, fontweight="bold")
    return _finalize(fig, show)


def plot_gold_ratios(df: pd.DataFrame, show: bool = True) -> plt.Figure:
    """Plot gold cross-asset ratio features if available."""
    ratio_cols = [
        "gold_silver_ratio",
        "gold_oil_ratio",
        "gold_sp500_ratio",
        "gold_dxy_ratio",
    ]
    available_cols = [column for column in ratio_cols if column in df.columns]

    if not available_cols:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.text(0.5, 0.5, "No ratio columns available", ha="center", va="center")
        ax.axis("off")
        return _finalize(fig, show)

    fig, axes = plt.subplots(1, len(available_cols), figsize=(16, 4))
    if len(available_cols) == 1:
        axes = [axes]

    for ax, column in zip(axes, available_cols):
        ax.plot(df.index, df[column], lw=1)
        ax.set_title(column.replace("_", " ").title())
        ax.grid(True, alpha=0.3)

    fig.suptitle("Gold Cross-Asset Ratios", fontsize=14, fontweight="bold")
    return _finalize(fig, show)


def plot_correlation_heatmap(df: pd.DataFrame, show: bool = True) -> plt.Figure:
    """Plot the lower triangle correlation heatmap for selected features."""
    key_features = [
        "gold_close",
        "sma_20",
        "rsi_14",
        "macd",
        "adx_14",
        "dxy_close",
        "us_10y_yield",
        "real_yield",
        "vix",
        "gold_silver_ratio",
        "gold_oil_ratio",
        "gold_pct_chg_5d",
        "gold_pct_chg_21d",
        "next_10_day_open_change_pct",
    ]
    available = [column for column in key_features if column in df.columns]

    if not available:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.text(0.5, 0.5, "No correlation features available", ha="center", va="center")
        ax.axis("off")
        return _finalize(fig, show)

    corr = df[available].corr()

    fig, ax = plt.subplots(figsize=(12, 10))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax, cbar_kws={"shrink": 0.8})
    ax.set_title("Feature Correlation Matrix (Lower Triangle)", fontsize=14)
    return _finalize(fig, show)


def plot_return_distributions(df: pd.DataFrame, show: bool = True) -> plt.Figure:
    """Plot histograms for available return windows."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    windows = [
        ("gold_pct_chg_5d", "Weekly Return % (5d)"),
        ("gold_pct_chg_21d", "Monthly Return % (21d)"),
        ("gold_pct_chg_63d", "Quarterly Return % (63d)"),
        ("gold_pct_chg_252d", "Yearly Return % (252d)"),
    ]

    for ax, (column, title) in zip(axes.flat, windows):
        if column in df.columns:
            data = df[column].dropna()
            ax.hist(data, bins=50, edgecolor="white", color="steelblue", alpha=0.8)
            ax.axvline(data.mean(), color="red", linestyle="--", label=f"Mean: {data.mean():.2f}%")
            ax.axvline(0, color="black", lw=0.8)
            ax.set_title(title)
            ax.set_xlabel("Return %")
            ax.legend()
            ax.grid(True, alpha=0.3)

    fig.suptitle("Gold Return Distribution by Time Window", fontsize=14, fontweight="bold")
    return _finalize(fig, show)


def print_target_label_statistics(df_targets: pd.DataFrame) -> None:
    """Print descriptive statistics for the target labels."""
    if df_targets.empty:
        print("=== Target Labels Statistics ===")
        print("No target label rows available")
        return

    print("=== Target Labels Statistics ===")
    print(df_targets.describe().T)



__all__ = [
    "plot_bollinger_bands",
    "plot_correlation_heatmap",
    "plot_gold_price_trend",
    "plot_gold_ratios",
    "plot_macro_factors_vs_gold",
    "plot_return_distributions",
    "plot_rsi_and_macd",
    "print_target_label_statistics",
    "setup_plot_style",
]
