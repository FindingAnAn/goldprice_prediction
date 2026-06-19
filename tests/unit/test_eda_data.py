from __future__ import annotations

import pandas as pd

from src.pipelines.eda_data import combine_with_targets


def test_combine_with_targets_excludes_duplicate_metadata():
    index = pd.date_range("2026-01-01", periods=2, name="date")
    features = pd.DataFrame(
        {"feature": [1.0, 2.0], "updated_at": [1, 2]},
        index=index,
    )
    targets = pd.DataFrame(
        {
            "next_7_day_price": [10.0, 11.0],
            "next_1_day_price": [8.0, 9.0],
            "updated_at": [3, 4],
        },
        index=index,
    )

    combined = combine_with_targets(features, targets)

    assert "next_7_day_price" in combined
    assert list(combined.columns).count("updated_at") == 1
