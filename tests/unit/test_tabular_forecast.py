import numpy as np
import pandas as pd

from src.modeling.tabular_forecast import (
    _training_bounds,
    build_tabular_feature_frame,
)


def test_tabular_features_use_only_current_and_historical_values():
    rows = 300
    index = pd.date_range("2020-01-01", periods=rows, freq="B")
    close = pd.Series(np.linspace(1000.0, 1300.0, rows), index=index)
    frame = pd.DataFrame(
        {
            "gold_open": close - 2.0,
            "gold_high": close + 4.0,
            "gold_low": close - 5.0,
            "gold_close": close,
            "gold_volume": np.linspace(100.0, 200.0, rows),
            "dxy_close": np.linspace(90.0, 100.0, rows),
        },
        index=index,
    )

    original = build_tabular_feature_frame(frame)
    changed = frame.copy()
    changed.iloc[-1, changed.columns.get_loc("gold_close")] = 9000.0
    rebuilt = build_tabular_feature_frame(changed)

    pd.testing.assert_series_equal(
        original.iloc[-2],
        rebuilt.iloc[-2],
        check_names=False,
    )
    assert not any(column.startswith("next_") for column in original.columns)


def test_tabular_features_include_month_quarter_and_year_windows():
    rows = 300
    index = pd.date_range("2020-01-01", periods=rows, freq="B")
    close = pd.Series(np.linspace(1000.0, 1300.0, rows), index=index)
    frame = pd.DataFrame(
        {
            "gold_open": close - 2.0,
            "gold_high": close + 4.0,
            "gold_low": close - 5.0,
            "gold_close": close,
            "gold_volume": np.linspace(100.0, 200.0, rows),
        },
        index=index,
    )

    result = build_tabular_feature_frame(frame)

    assert "gold_return_volatility_21d" in result
    assert "gold_return_volatility_63d" in result
    assert "gold_return_volatility_252d" in result


def test_training_bounds_purge_unavailable_horizon_labels():
    training_start, training_end = _training_bounds(
        cutoff=2000,
        horizon=10,
    )

    assert training_end == 1990
    assert training_end - training_start + 1 == 1260
