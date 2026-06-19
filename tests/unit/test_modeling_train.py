from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin

from src.modeling.train import (
    ReturnTargetRegressor,
    build_training_frame,
    evaluate_holdout_model,
    infer_feature_columns,
    time_series_train_test_split,
    train_and_select_best,
    validate_feature_columns,
)


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
            "next_7_day_price": np.arange(12, dtype=float) + 7,
            "next_7_day_direction": np.ones(12, dtype=float),
            "cpi": np.arange(200, 212, dtype=float),
        },
        index=index,
    )


def test_time_series_split_returns_chronological_parts():
    frame = _sample_frame()
    train_df, test_df = time_series_train_test_split(frame, test_size=0.25)

    assert len(train_df) == 9
    assert len(test_df) == 3
    assert train_df.index.max() < test_df.index.min()


def test_train_and_select_best_uses_best_candidate(monkeypatch, tmp_path):
    frame = _sample_frame()
    monkeypatch.setattr("src.modeling.train.MODELS_DIR", tmp_path)
    monkeypatch.setattr("src.modeling.train.MODEL_REPORT_DIR", tmp_path)

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


def test_infer_feature_columns_excludes_all_future_labels():
    frame = _sample_frame()

    feature_cols = infer_feature_columns(frame, target_col="next_7_day_price")

    assert feature_cols == ["f1", "f2"]


def test_current_gold_close_is_valid_after_close_feature():
    frame = _sample_frame().assign(gold_close=np.arange(12, dtype=float))

    feature_cols = infer_feature_columns(frame, target_col="next_7_day_price")

    assert "gold_close" in feature_cols


def test_validate_feature_columns_rejects_point_in_time_unsafe_macro():
    with np.testing.assert_raises(ValueError):
        validate_feature_columns(["f1", "cpi"])


def test_build_training_frame_keeps_only_selected_target():
    index = pd.date_range("2024-01-01", periods=3, freq="D")
    features = pd.DataFrame({"f1": [1.0, 2.0, 3.0]}, index=index)
    targets = pd.DataFrame(
        {
            "next_1_day_price": [2.0, 3.0, 4.0],
            "next_7_day_price": [8.0, 9.0, 10.0],
        },
        index=index,
    )

    frame = build_training_frame(
        master_features=features,
        target_labels=targets,
        target_col="next_7_day_price",
    )

    assert list(frame.columns) == ["f1", "next_7_day_price"]


def test_time_series_split_purges_forecast_gap():
    frame = _sample_frame()
    train_df, test_df = time_series_train_test_split(
        frame,
        test_size=0.25,
        gap=2,
    )

    assert len(train_df) == 7
    assert len(test_df) == 3
    assert test_df.index.min() - train_df.index.max() == pd.Timedelta(days=3)


def test_evaluate_holdout_model_returns_rmse():
    frame = _sample_frame()
    model = FirstFeatureRegressor().fit(frame[["f1", "f2"]].to_numpy(), frame["next_1_day_price"].to_numpy())

    metrics = evaluate_holdout_model(model, frame, feature_cols=["f1", "f2"], target_col="next_1_day_price", test_size=0.25)

    assert set(metrics) == {"rmse"}
    assert metrics["rmse"] >= 0


def test_evaluate_holdout_rejects_full_data_production_model():
    frame = _sample_frame()
    model = FirstFeatureRegressor().fit(
        frame[["f1", "f2"]].to_numpy(),
        frame["next_1_day_price"].to_numpy(),
    )
    model._gold_fit_scope = "full_labeled_data"

    with np.testing.assert_raises(ValueError):
        evaluate_holdout_model(
            model,
            frame,
            feature_cols=["f1", "f2"],
            target_col="next_1_day_price",
            test_size=0.25,
        )


def test_return_target_regressor_reconstructs_future_price():
    X = np.array([[100.0], [200.0], [300.0]])
    y = np.array([110.0, 220.0, 330.0])
    model = ReturnTargetRegressor(
        base_estimator=ConstantRegressor(constant=10.0),
        current_price_index=0,
    ).fit(X, y)

    np.testing.assert_allclose(model.predict(X), y)
