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
                    f"DXY {'giảm' if dxy < 0 else 'tăng'} {abs(dxy):.2f}% "
                    "trong 5 phiên, "
                    f"{'giảm' if dxy < 0 else 'tăng'} áp lực tỷ giá lên vàng."
                ),
            )
        )

    real_yield = _finite(row, "real_yield_change_5d")
    if real_yield is not None:
        evidence.append(
            DriverEvidence(
                score_for_gold=float(np.clip(-real_yield / 0.10, -3.0, 3.0)),
                reason=(
                    f"Real yield {'giảm' if real_yield < 0 else 'tăng'} "
                    f"{abs(real_yield):.2f} điểm %, "
                    f"{'giảm' if real_yield < 0 else 'tăng'} chi phí cơ hội "
                    "nắm giữ vàng."
                ),
            )
        )

    vix = _finite(row, "vix_change_5d")
    if vix is not None:
        evidence.append(
            DriverEvidence(
                score_for_gold=float(np.clip(vix / 10.0, -3.0, 3.0)),
                reason=(
                    f"VIX {'tăng' if vix > 0 else 'giảm'} {abs(vix):.2f}% "
                    "trong 5 phiên, phản ánh "
                    f"{'nhu cầu trú ẩn cao hơn' if vix > 0 else 'rủi ro thị trường hạ nhiệt'}."
                ),
            )
        )

    epu = _finite(row, "epu_zscore_63d")
    if epu is not None:
        evidence.append(
            DriverEvidence(
                score_for_gold=float(np.clip(epu, -3.0, 3.0)),
                reason=(
                    f"Chỉ số bất định chính sách ở mức {epu:+.2f} độ lệch chuẩn "
                    "so với 63 phiên, "
                    f"{'hỗ trợ' if epu > 0 else 'làm yếu'} nhu cầu phòng thủ."
                ),
            )
        )

    credit = _finite(row, "high_yield_spread_change_5d")
    if credit is not None:
        evidence.append(
            DriverEvidence(
                score_for_gold=float(np.clip(credit / 0.20, -3.0, 3.0)),
                reason=(
                    f"High-yield spread {'mở rộng' if credit > 0 else 'thu hẹp'} "
                    f"{abs(credit):.2f} điểm %, cho thấy "
                    f"{'credit stress tăng' if credit > 0 else 'khẩu vị rủi ro cải thiện'}."
                ),
            )
        )

    positioning = _finite(row, "cftc_mm_net_change_pct_oi")
    if positioning is not None:
        evidence.append(
            DriverEvidence(
                score_for_gold=float(np.clip(positioning / 2.0, -3.0, 3.0)),
                reason=(
                    f"Managed Money CFTC {'tăng' if positioning > 0 else 'giảm'} "
                    f"net position {abs(positioning):.2f}% open interest."
                ),
            )
        )

    gld_return = _finite(row, "gld_return_5d")
    gld_volume = _finite(row, "gld_volume_zscore_21d")
    if gld_return is not None:
        volume_text = (
            f", volume GLD ở mức {gld_volume:+.2f} độ lệch chuẩn"
            if gld_volume is not None
            else ""
        )
        evidence.append(
            DriverEvidence(
                score_for_gold=float(np.clip(gld_return / 2.0, -3.0, 3.0)),
                reason=(
                    f"GLD {'tăng' if gld_return > 0 else 'giảm'} "
                    f"{abs(gld_return):.2f}% trong 5 phiên{volume_text}, "
                    "đại diện dòng tiền ETF vàng."
                ),
            )
        )
    return evidence


def _top_reasons(
    evidence: list[DriverEvidence],
    direction: str,
) -> list[str]:
    if direction == "TĂNG":
        ranked = sorted(evidence, key=lambda item: item.score_for_gold, reverse=True)
    elif direction == "GIẢM":
        ranked = sorted(evidence, key=lambda item: item.score_for_gold)
    else:
        ranked = sorted(
            evidence,
            key=lambda item: abs(item.score_for_gold),
            reverse=True,
        )
    return [item.reason for item in ranked[:3]]


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
        ["TĂNG", "GIẢM"],
        default="ĐI NGANG",
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
    output["explanation_method"] = "economic_driver_score_v1_non_causal"
    return output


__all__ = ["DriverEvidence", "add_forecast_context"]
