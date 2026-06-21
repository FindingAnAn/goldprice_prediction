"""Economically grounded directional context for gold forecasts."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from config.settings import OPEN_FORECAST_FLAT_THRESHOLD_PCT


@dataclass(frozen=True)
class DriverEvidence:
    score_for_gold: float
    reason: str


def _finite(row: pd.Series, column: str) -> float | None:
    value = row.get(column)
    if value is None or pd.isna(value):
        return None
    numeric = float(value)
    if not np.isfinite(numeric):
        return None
    return numeric


def _driver_evidence(row: pd.Series) -> list[DriverEvidence]:
    evidence: list[DriverEvidence] = []

    dxy = _finite(row, "dxy_return_5d")
    if dxy is not None:
        evidence.append(
            DriverEvidence(
                score_for_gold=float(np.clip(-dxy / 1.0, -3.0, 3.0)),
                reason=(
                    f"DXY {'fell' if dxy < 0 else 'rose'} {abs(dxy):.2f}% "
                    "over five sessions, "
                    f"{'reducing' if dxy < 0 else 'increasing'} currency "
                    "pressure on gold."
                ),
            )
        )

    real_yield = _finite(row, "real_yield_change_5d")
    if real_yield is not None:
        evidence.append(
            DriverEvidence(
                score_for_gold=float(np.clip(-real_yield / 0.10, -3.0, 3.0)),
                reason=(
                    f"Real yield {'fell' if real_yield < 0 else 'rose'} "
                    f"{abs(real_yield):.2f} percentage points, "
                    f"{'reducing' if real_yield < 0 else 'increasing'} the "
                    "opportunity cost of holding gold."
                ),
            )
        )

    vix = _finite(row, "vix_change_5d")
    if vix is not None:
        evidence.append(
            DriverEvidence(
                score_for_gold=float(np.clip(vix / 10.0, -3.0, 3.0)),
                reason=(
                    f"VIX {'rose' if vix > 0 else 'fell'} {abs(vix):.2f}% "
                    "over five sessions, indicating "
                    f"{'stronger safe-haven demand' if vix > 0 else 'lower market stress'}."
                ),
            )
        )

    epu = _finite(row, "epu_zscore_63d")
    if epu is not None:
        evidence.append(
            DriverEvidence(
                score_for_gold=float(np.clip(epu, -3.0, 3.0)),
                reason=(
                    f"Economic policy uncertainty is {epu:+.2f} standard "
                    "deviations versus its 63-session history, "
                    f"{'supporting' if epu > 0 else 'weakening'} defensive demand."
                ),
            )
        )

    credit = _finite(row, "high_yield_spread_change_5d")
    if credit is not None:
        evidence.append(
            DriverEvidence(
                score_for_gold=float(np.clip(credit / 0.20, -3.0, 3.0)),
                reason=(
                    f"The high-yield spread {'widened' if credit > 0 else 'narrowed'} "
                    f"{abs(credit):.2f} percentage points, indicating "
                    f"{'higher credit stress' if credit > 0 else 'improved risk appetite'}."
                ),
            )
        )

    positioning = _finite(row, "cftc_mm_net_change_pct_oi")
    if positioning is not None:
        evidence.append(
            DriverEvidence(
                score_for_gold=float(np.clip(positioning / 2.0, -3.0, 3.0)),
                reason=(
                    f"CFTC Managed Money net positioning "
                    f"{'increased' if positioning > 0 else 'decreased'} by "
                    f"{abs(positioning):.2f}% of open interest."
                ),
            )
        )

    gld_return = _finite(row, "gld_return_5d")
    gld_volume = _finite(row, "gld_volume_zscore_21d")
    if gld_return is not None:
        volume_text = (
            f", with GLD volume at {gld_volume:+.2f} standard deviations"
            if gld_volume is not None
            else ""
        )
        evidence.append(
            DriverEvidence(
                score_for_gold=float(np.clip(gld_return / 2.0, -3.0, 3.0)),
                reason=(
                    f"GLD {'rose' if gld_return > 0 else 'fell'} "
                    f"{abs(gld_return):.2f}% over five sessions{volume_text}, "
                    "providing a proxy for gold ETF flows."
                ),
            )
        )
    return evidence


def _top_reasons(
    evidence: list[DriverEvidence],
    direction: str,
) -> list[str]:
    if direction == "UP":
        supporting = sorted(
            (item for item in evidence if item.score_for_gold > 0),
            key=lambda item: item.score_for_gold,
            reverse=True,
        )
        opposing = sorted(
            (item for item in evidence if item.score_for_gold <= 0),
            key=lambda item: item.score_for_gold,
        )
    elif direction == "DOWN":
        supporting = sorted(
            (item for item in evidence if item.score_for_gold < 0),
            key=lambda item: item.score_for_gold,
        )
        opposing = sorted(
            (item for item in evidence if item.score_for_gold >= 0),
            key=lambda item: item.score_for_gold,
            reverse=True,
        )
    else:
        neutral = sorted(
            evidence,
            key=lambda item: abs(item.score_for_gold),
            reverse=True,
        )
        return [item.reason for item in neutral[:3]]

    reasons = [item.reason for item in supporting[:3]]
    if len(reasons) < 3:
        reasons.extend(
            f"Counter-signal: {item.reason}"
            for item in opposing[: 3 - len(reasons)]
        )
    return reasons


def add_forecast_context(
    predictions: pd.DataFrame,
    feature_frame: pd.DataFrame,
) -> pd.DataFrame:
    """Add current-price deltas and transparent economic driver context.

    Reasons are directional economic evidence, not causal attribution or SHAP
    values. This distinction is persisted through ``explanation_method``.
    """

    output = predictions.copy()
    latest = feature_frame.sort_index().iloc[-1]
    current_close = float(latest["gold_close"])
    output["reference_close"] = current_close
    output["predicted_change_amount"] = output["predicted_open"] - current_close
    output["predicted_change_pct"] = (
        100.0 * output["predicted_change_amount"] / current_close
    )
    output["forecast_direction"] = np.select(
        [
            output["predicted_change_pct"] > OPEN_FORECAST_FLAT_THRESHOLD_PCT,
            output["predicted_change_pct"] < -OPEN_FORECAST_FLAT_THRESHOLD_PCT,
        ],
        ["UP", "DOWN"],
        default="FLAT",
    )

    evidence = _driver_evidence(latest)
    reasons = [
        _top_reasons(evidence, str(direction))
        for direction in output["forecast_direction"]
    ]
    for reason_index in range(3):
        output[f"top_reason_{reason_index + 1}"] = [
            row[reason_index] if reason_index < len(row) else None
            for row in reasons
        ]
    output["explanation_method"] = "economic_driver_score_v2_non_causal"
    return output


__all__ = ["DriverEvidence", "add_forecast_context"]
