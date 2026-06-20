import numpy as np
import pandas as pd

from src.modeling.sequence_forecast import _prepare_sequence_data


def test_sparse_exogenous_feature_does_not_truncate_full_history():
    rows = 400
    index = pd.date_range("2010-01-01", periods=rows, freq="B")
    frame = pd.DataFrame(
        {
            "gold_open": np.linspace(1000.0, 1400.0, rows),
            "gold_close": np.linspace(1001.0, 1401.0, rows),
            "dxy_close": [np.nan] * 350 + list(np.linspace(90.0, 100.0, 50)),
        },
        index=index,
    )

    sequence, _, used, excluded = _prepare_sequence_data(frame)

    assert len(sequence) == rows
    assert "gold_close" in used
    assert "dxy_close" in excluded
