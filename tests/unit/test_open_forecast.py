from __future__ import annotations

import numpy as np
import pandas as pd

from src.modeling.open_forecast import (
    MultiHorizonPersistenceRegressor,
    next_estimated_session_dates,
)
from src.modeling.time_series import infer_feature_columns


def test_multi_horizon_persistence_repeats_current_close():
    X = np.array([[100.0, 1.0], [200.0, 2.0]])
    model = MultiHorizonPersistenceRegressor(
        current_price_index=0,
        horizon=3,
    ).fit(X, np.zeros((2, 3)))

    np.testing.assert_allclose(
        model.predict(X),
        np.array([[100.0, 100.0, 100.0], [200.0, 200.0, 200.0]]),
    )


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
