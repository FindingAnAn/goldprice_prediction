"""Analyse calendar, seasonal and market-regime similarities in gold returns."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipelines.eda_data import (
    add_open_target_changes,
    combine_with_targets,
    load_master_features,
    load_target_labels,
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "predictions" / "similarity"
HORIZONS = (1, 3, 5, 7, 10)


def _summary(
    frame: pd.DataFrame,
    group_columns: list[str],
    target: str,
) -> pd.DataFrame:
    grouped = frame.dropna(subset=[target]).groupby(group_columns)[target]
    result = grouped.agg(["count", "mean", "median", "std"]).reset_index()
    up_rate = grouped.apply(lambda values: float((values > 0).mean())).reset_index(
        name="up_rate"
    )
    result = result.merge(up_rate, on=group_columns, how="left")
    result["t_stat"] = result["mean"] / (
        result["std"] / np.sqrt(result["count"])
    )
    return result


def _calendar_position(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["year"] = result.index.year
    result["month"] = result.index.month
    result["quarter"] = result.index.quarter
    result["trading_day_in_month"] = result.groupby(
        [result.index.year, result.index.month]
    ).cumcount() + 1
    result["trading_days_left_month"] = result.groupby(
        ["year", "month"]
    ).cumcount(ascending=False)
    result["trading_day_in_year"] = result.groupby(result.index.year).cumcount() + 1
    result["trading_days_left_year"] = result.groupby("year").cumcount(
        ascending=False
    )
    result["calendar_event"] = "middle_of_period"
    result.loc[result["trading_day_in_month"] <= 5, "calendar_event"] = "month_start_5"
    result.loc[result["trading_days_left_month"] < 5, "calendar_event"] = "month_end_5"
    result.loc[result["trading_days_left_year"] < 10, "calendar_event"] = "year_end_10"
    return result


def _regime_columns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["momentum_regime"] = pd.cut(
        result["gold_pct_chg_21d"],
        bins=[-np.inf, -5.0, 0.0, 5.0, np.inf],
        labels=["strong_down", "down", "up", "strong_up"],
    )
    result["vix_regime"] = pd.cut(
        result["vix"],
        bins=[-np.inf, 15.0, 25.0, np.inf],
        labels=["low", "normal", "high"],
    )
    result["real_yield_regime"] = pd.cut(
        result["real_yield"],
        bins=[-np.inf, 0.0, 1.5, np.inf],
        labels=["negative", "moderate", "high"],
    )
    result["dxy_regime"] = pd.cut(
        result["gold_dxy_ratio"].pct_change(21) * 100.0,
        bins=[-np.inf, -3.0, 3.0, np.inf],
        labels=["dollar_outperform", "neutral", "gold_outperform"],
    )
    return result


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    master = load_master_features()
    targets = load_target_labels(target_col="next_10_day_open")
    frame = add_open_target_changes(
        combine_with_targets(master, targets)
    ).sort_index()
    frame = _regime_columns(_calendar_position(frame))

    monthly_outputs: list[pd.DataFrame] = []
    quarterly_outputs: list[pd.DataFrame] = []
    event_outputs: list[pd.DataFrame] = []
    regime_outputs: list[pd.DataFrame] = []

    for horizon in HORIZONS:
        target = f"next_{horizon}_day_open_change_pct"
        monthly = _summary(frame, ["month"], target)
        per_year_month = (
            frame.dropna(subset=[target])
            .groupby(["year", "month"])[target]
            .mean()
            .reset_index()
        )
        consistency = (
            per_year_month.groupby("month")[target]
            .agg(
                years="count",
                year_mean="mean",
                year_median="median",
                positive_year_rate=lambda values: float((values > 0).mean()),
            )
            .reset_index()
        )
        monthly = monthly.merge(consistency, on="month", how="left")
        monthly["horizon"] = horizon
        monthly_outputs.append(monthly)

        quarterly = _summary(frame, ["quarter"], target)
        quarterly["horizon"] = horizon
        quarterly_outputs.append(quarterly)

        events = _summary(frame, ["calendar_event"], target)
        events["horizon"] = horizon
        event_outputs.append(events)

        for regime_column in (
            "momentum_regime",
            "vix_regime",
            "real_yield_regime",
            "dxy_regime",
        ):
            regime = _summary(frame, [regime_column], target)
            regime = regime.rename(columns={regime_column: "regime_value"})
            regime["regime_type"] = regime_column
            regime["horizon"] = horizon
            regime_outputs.append(regime)

    monthly_result = pd.concat(monthly_outputs, ignore_index=True)
    quarterly_result = pd.concat(quarterly_outputs, ignore_index=True)
    event_result = pd.concat(event_outputs, ignore_index=True)
    regime_result = pd.concat(regime_outputs, ignore_index=True)

    monthly_result.to_csv(OUTPUT_DIR / "monthly_seasonality.csv", index=False)
    quarterly_result.to_csv(OUTPUT_DIR / "quarterly_seasonality.csv", index=False)
    event_result.to_csv(OUTPUT_DIR / "calendar_events.csv", index=False)
    regime_result.to_csv(OUTPUT_DIR / "market_regimes.csv", index=False)

    analog_columns = [
        column
        for column in master.columns
        if column.startswith(("same_", "regime_"))
    ]
    current_analogs = master[analog_columns].tail(1).T
    current_analogs.columns = ["latest_value"]
    current_analogs.to_csv(OUTPUT_DIR / "latest_analogs.csv")

    print("=== MONTHLY EFFECTS WITH HIGHEST ABSOLUTE t-STAT ===")
    print(
        monthly_result.reindex(
            monthly_result["t_stat"].abs().sort_values(ascending=False).index
        )
        .head(20)
        .to_string(index=False)
    )
    print("\n=== CALENDAR EVENTS ===")
    print(event_result.to_string(index=False))
    print("\n=== CURRENT LEAKAGE-SAFE ANALOG FEATURES ===")
    print(current_analogs.to_string())
    print(f"\nSaved: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
