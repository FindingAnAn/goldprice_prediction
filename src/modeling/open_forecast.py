"""Helpers for formatting the selected sequence-model forecast."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay

from config.settings import OPEN_FORECAST_HORIZON


def next_estimated_session_dates(
    as_of_date: date | pd.Timestamp,
    periods: int = OPEN_FORECAST_HORIZON,
) -> pd.DatetimeIndex:
    """Estimate future sessions using the US federal business calendar."""

    business_day = CustomBusinessDay(calendar=USFederalHolidayCalendar())
    return pd.date_range(
        start=pd.Timestamp(as_of_date) + business_day,
        periods=periods,
        freq=business_day,
    )


def build_sequence_forecast_frame(
    selected_model: str,
    future_predictions: pd.DataFrame,
    rolling_predictions: pd.DataFrame,
    as_of_date: date | pd.Timestamp,
) -> pd.DataFrame:
    """Build the persisted 10-session forecast and empirical intervals."""

    if selected_model not in future_predictions.columns:
        raise KeyError(f"Missing future predictions for {selected_model}")
    if selected_model not in rolling_predictions.columns:
        raise KeyError(f"Missing rolling predictions for {selected_model}")

    residuals = rolling_predictions.assign(
        absolute_residual=lambda data: np.abs(
            data["actual_price"] - data[selected_model]
        )
    )
    steps = pd.Index(range(1, OPEN_FORECAST_HORIZON + 1), name="step")
    interval_80 = (
        residuals.groupby("step")["absolute_residual"]
        .quantile(0.80)
        .reindex(steps)
        .to_numpy()
    )
    interval_95 = (
        residuals.groupby("step")["absolute_residual"]
        .quantile(0.95)
        .reindex(steps)
        .to_numpy()
    )
    point_forecast = (
        future_predictions.sort_values("step")[selected_model]
        .head(OPEN_FORECAST_HORIZON)
        .to_numpy(dtype=float)
    )
    if len(point_forecast) != OPEN_FORECAST_HORIZON:
        raise ValueError(
            f"Expected {OPEN_FORECAST_HORIZON} future predictions, "
            f"received {len(point_forecast)}"
        )

    forecast_dates = next_estimated_session_dates(as_of_date)
    return pd.DataFrame(
        {
            "as_of_date": pd.Timestamp(as_of_date).date(),
            "forecast_step": np.arange(1, OPEN_FORECAST_HORIZON + 1),
            "forecast_date": forecast_dates.date,
            "predicted_open": point_forecast,
            "lower_80": point_forecast - interval_80,
            "upper_80": point_forecast + interval_80,
            "lower_95": point_forecast - interval_95,
            "upper_95": point_forecast + interval_95,
            "is_estimated_date": True,
        }
    )


__all__ = ["build_sequence_forecast_frame", "next_estimated_session_dates"]
