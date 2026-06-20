from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor

from src.modeling.open_forecast import (
    MultiHorizonPersistenceRegressor,
    MultiHorizonReturnRegressor,
    next_estimated_session_dates,
)
from src.modeling.train import infer_feature_columns


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


def test_multi_horizon_return_regressor_reconstructs_open_prices():
    X = np.array([[100.0], [200.0], [300.0]])
    y = np.array(
        [
            [101.0, 102.0],
            [202.0, 204.0],
            [303.0, 306.0],
        ]
    )
    model = MultiHorizonReturnRegressor(
        base_estimator=DummyRegressor(strategy="mean"),
        current_price_index=0,
    ).fit(X, y)

    np.testing.assert_allclose(model.predict(X), y)


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
