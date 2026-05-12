from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin

from src.modeling.train import evaluate_holdout_model, time_series_train_test_split, train_and_select_best


class ConstantRegressor(BaseEstimator, RegressorMixin):
    def __init__(self, constant: float = 0.0):
        self.constant = constant

    def fit(self, X, y):
        return self

    def predict(self, X):
        return np.full(shape=(len(X),), fill_value=self.constant, dtype=float)


class FirstFeatureRegressor(BaseEstimator, RegressorMixin):
    def fit(self, X, y):
        return self

    def predict(self, X):
        return np.asarray(X[:, 0], dtype=float)


def _sample_frame() -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=12, freq="D")
    return pd.DataFrame(
        {
            "f1": np.arange(12, dtype=float),
            "f2": np.arange(100, 112, dtype=float),
            "next_1_day_price": np.arange(12, dtype=float),
        },
        index=index,
    )


def test_time_series_split_returns_chronological_parts():
    frame = _sample_frame()
    train_df, test_df = time_series_train_test_split(frame, test_size=0.25)

    assert len(train_df) == 9
    assert len(test_df) == 3
    assert train_df.index.max() < test_df.index.min()


def test_train_and_select_best_uses_best_candidate():
    frame = _sample_frame()

    def candidate_factory():
        return {
            "constant": ConstantRegressor(constant=0.0),
            "feature": FirstFeatureRegressor(),
        }

    result = train_and_select_best(
        df=frame,
        target_col="next_1_day_price",
        candidate_factory=candidate_factory,
        use_optuna=False,
        test_size=0.25,
    )

    assert result.name == "feature"
    assert result.cv_rmse >= 0
    assert result.test_rmse >= 0


def test_evaluate_holdout_model_returns_rmse():
    frame = _sample_frame()
    model = FirstFeatureRegressor().fit(frame[["f1", "f2"]].to_numpy(), frame["next_1_day_price"].to_numpy())

    metrics = evaluate_holdout_model(model, frame, feature_cols=["f1", "f2"], target_col="next_1_day_price", test_size=0.25)

    assert set(metrics) == {"rmse"}
    assert metrics["rmse"] >= 0
