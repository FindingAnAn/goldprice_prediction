import pandas as pd

from src.modeling.forecast_explanations import add_forecast_context


def test_forecast_context_adds_direction_changes_and_three_reasons():
    features = pd.DataFrame(
        {
            "gold_close": [100.0],
            "dxy_return_5d": [-1.0],
            "real_yield_change_5d": [-0.2],
            "vix_change_5d": [15.0],
            "epu_zscore_63d": [1.5],
            "high_yield_spread_change_5d": [0.1],
            "cftc_mm_net_change_pct_oi": [2.0],
            "gld_return_5d": [1.0],
            "gld_volume_zscore_21d": [0.5],
        },
        index=pd.to_datetime(["2026-06-18"]),
    )
    predictions = pd.DataFrame(
        {
            "predicted_open": [102.0],
            "forecast_step": [1],
        }
    )

    result = add_forecast_context(predictions, features)

    assert result.iloc[0]["forecast_direction"] == "UP"
    assert result.iloc[0]["predicted_change_amount"] == 2.0
    assert result.iloc[0]["predicted_change_pct"] == 2.0
    assert all(result.iloc[0][f"top_reason_{index}"] for index in range(1, 4))
    assert "Real yield" in result.iloc[0]["top_reason_1"]
    assert result.iloc[0]["explanation_method"].endswith("non_causal")
