from __future__ import annotations

import numpy as np
import pandas as pd

from src.modeling.open_forecast import (
    build_sequence_forecast_frame,
    next_estimated_session_dates,
)
from src.modeling.time_series import infer_feature_columns


def test_open_targets_are_never_inferred_as_features():
    frame = pd.DataFrame(
        {
            "gold_close": [100.0, 101.0],
            "next_1_day_open": [101.0, 102.0],
            "next_10_day_open": [110.0, 111.0],
        }
    )

    assert infer_feature_columns(frame, "next_1_day_open") == ["gold_close"]


def test_future_session_dates_skip_weekend_and_us_federal_holiday():
    dates = next_estimated_session_dates(pd.Timestamp("2026-06-18"), periods=2)

    assert [value.date().isoformat() for value in dates] == [
        "2026-06-22",
        "2026-06-23",
    ]


def test_build_sequence_forecast_uses_selected_model_and_residuals():
    future = pd.DataFrame(
        {
            "step": range(1, 11),
            "TiDE": np.arange(101.0, 111.0),
        }
    )
    rolling = pd.DataFrame(
        {
            "step": list(range(1, 11)) * 2,
            "actual_price": np.arange(100.0, 120.0),
            "TiDE": np.arange(99.0, 119.0),
        }
    )

    result = build_sequence_forecast_frame(
        selected_model="TiDE",
        future_predictions=future,
        rolling_predictions=rolling,
        as_of_date=pd.Timestamp("2026-06-19"),
    )

    assert len(result) == 10
    assert result.iloc[0]["predicted_open"] == 101.0
    assert result.iloc[0]["lower_80"] == 100.0
