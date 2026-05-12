from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin

from src.modeling.predict import predict_frame, predict_latest


class SumRegressor(BaseEstimator, RegressorMixin):
    def fit(self, X, y):
        return self

    def predict(self, X):
        return np.asarray(X[:, 0] + X[:, 1], dtype=float)


def _sample_frame() -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=4, freq="D")
    return pd.DataFrame(
        {
            "f1": [1.0, 2.0, 3.0, 4.0],
            "f2": [10.0, 20.0, 30.0, 40.0],
        },
        index=index,
    )


def test_predict_frame_returns_latest_rows_without_persisting(tmp_path):
    frame = _sample_frame()
    model = SumRegressor()

    output = predict_frame(
        model=model,
        feature_frame=frame,
        feature_cols=["f1", "f2"],
        latest_n=2,
        persist=False,
    )

    assert list(output.columns) == ["prediction"]
    assert len(output) == 2
    assert output.iloc[0, 0] == 33.0


def test_predict_latest_uses_injected_frame_and_model(monkeypatch, tmp_path):
    frame = _sample_frame()
    model = SumRegressor()

    monkeypatch.setattr("src.modeling.predict.load_master_features", lambda: frame)
    monkeypatch.setattr("src.modeling.predict.load_best_model", lambda path=None: model)

    output = predict_latest(model=None, feature_cols=["f1", "f2"], latest_n=1, persist=False)

    assert len(output) == 1
    assert output.iloc[0, 0] == 44.0
