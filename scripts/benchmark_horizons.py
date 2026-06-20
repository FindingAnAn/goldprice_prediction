"""Compare practical forecast horizons with leakage-safe chronological tests."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Lasso
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import SUPPORTED_FORECAST_HORIZONS
from src.modeling.train import (
    AnalogReturnRegressor,
    FeatureColumnRegressor,
    ReturnTargetRegressor,
    build_training_frame,
    infer_feature_columns,
    time_series_train_test_split,
)

OUTPUT_PATH = PROJECT_ROOT / "data" / "predictions" / "horizon_benchmark.csv"


def _candidate_models(
    feature_cols: list[str],
    horizon: int,
) -> dict[str, object]:
    current_price_index = feature_cols.index("gold_close")
    candidates: dict[str, object] = {
        "persistence": FeatureColumnRegressor(current_price_index),
        "return_lasso": ReturnTargetRegressor(
            Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
                    ("scaler", StandardScaler()),
                    (
                        "model",
                        Lasso(
                            alpha=0.01,
                            max_iter=10_000,
                            tol=1e-3,
                            selection="random",
                            random_state=42,
                        ),
                    ),
                ]
            ),
            current_price_index=current_price_index,
        ),
        "return_extra_trees": ReturnTargetRegressor(
            Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
                    (
                        "model",
                        ExtraTreesRegressor(
                            n_estimators=150,
                            min_samples_leaf=3,
                            max_features=0.7,
                            random_state=42,
                            n_jobs=-1,
                        ),
                    ),
                ]
            ),
            current_price_index=current_price_index,
        ),
    }

    analog_column = f"same_doy_return_{horizon}d_mean"
    if analog_column in feature_cols:
        candidates["same_doy_analog"] = AnalogReturnRegressor(
            current_price_index=current_price_index,
            analog_return_index=feature_cols.index(analog_column),
        )

    try:
        from catboost import CatBoostRegressor

        candidates["return_catboost"] = ReturnTargetRegressor(
            CatBoostRegressor(
                iterations=300,
                depth=6,
                learning_rate=0.03,
                loss_function="RMSE",
                random_seed=42,
                verbose=False,
                allow_writing_files=False,
            ),
            current_price_index=current_price_index,
        )
    except ImportError:
        pass

    return candidates


def _direction_accuracy(
    current_price: np.ndarray,
    actual: np.ndarray,
    prediction: np.ndarray,
) -> float:
    if np.allclose(prediction, current_price):
        return float("nan")
    actual_direction = np.sign(actual - current_price)
    predicted_direction = np.sign(prediction - current_price)
    return float(np.mean(actual_direction == predicted_direction))


def benchmark_horizons(
    horizons: tuple[int, ...] = SUPPORTED_FORECAST_HORIZONS,
    test_size: float = 0.2,
) -> pd.DataFrame:
    rows: list[dict[str, float | int | str | bool]] = []

    for horizon in horizons:
        target_col = f"next_{horizon}_day_price"
        frame = build_training_frame(target_col=target_col).sort_index()
        feature_cols = infer_feature_columns(frame, target_col)
        required = [
            column
            for column in ("gold_close", "gold_open", "gold_high", "gold_low")
            if column in feature_cols
        ]
        modeling_frame = frame.dropna(subset=required + [target_col])
        train, test = time_series_train_test_split(
            modeling_frame,
            test_size=test_size,
            gap=horizon,
        )
        X_train = train[feature_cols].to_numpy()
        y_train = train[target_col].to_numpy()
        X_test = test[feature_cols].to_numpy()
        y_test = test[target_col].to_numpy()
        current_test = test["gold_close"].to_numpy()
        cv = TimeSeriesSplit(n_splits=3, gap=horizon)

        horizon_rows: list[dict[str, float | int | str | bool]] = []
        for name, model in _candidate_models(feature_cols, horizon).items():
            cv_rmse = float(
                -np.mean(
                    cross_val_score(
                        model,
                        X_train,
                        y_train,
                        cv=cv,
                        scoring="neg_root_mean_squared_error",
                    )
                )
            )
            model.fit(X_train, y_train)
            prediction = np.asarray(model.predict(X_test), dtype=float)
            rmse = float(np.sqrt(mean_squared_error(y_test, prediction)))
            mae = float(mean_absolute_error(y_test, prediction))
            mape = float(np.mean(np.abs((y_test - prediction) / y_test)) * 100.0)
            direction_accuracy = _direction_accuracy(
                current_test,
                y_test,
                prediction,
            )
            horizon_rows.append(
                {
                    "horizon": horizon,
                    "model": name,
                    "cv_rmse": cv_rmse,
                    "test_rmse": rmse,
                    "test_mae": mae,
                    "test_mape": mape,
                    "direction_accuracy": direction_accuracy,
                    "test_rows": len(test),
                    "selected_by_cv": False,
                }
            )

        selected_index = int(
            np.argmin([float(item["cv_rmse"]) for item in horizon_rows])
        )
        horizon_rows[selected_index]["selected_by_cv"] = True
        persistence_rmse = next(
            float(item["test_rmse"])
            for item in horizon_rows
            if item["model"] == "persistence"
        )
        for item in horizon_rows:
            item["rmse_improvement_vs_persistence_pct"] = (
                100.0
                * (persistence_rmse - float(item["test_rmse"]))
                / persistence_rmse
            )
        rows.extend(horizon_rows)

    result = pd.DataFrame(rows).sort_values(["horizon", "cv_rmse"])
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)
    return result


if __name__ == "__main__":
    benchmark = benchmark_horizons()
    selected = benchmark[benchmark["selected_by_cv"]].copy()
    print("=== MODEL SELECTED BY CV FOR EACH HORIZON ===")
    print(
        selected[
            [
                "horizon",
                "model",
                "cv_rmse",
                "test_rmse",
                "test_mape",
                "direction_accuracy",
                "rmse_improvement_vs_persistence_pct",
            ]
        ].to_string(index=False)
    )
    print(f"\nSaved: {OUTPUT_PATH}")
