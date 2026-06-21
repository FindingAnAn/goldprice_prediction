"""Shared leakage-safe utilities for time-series modeling."""

from __future__ import annotations

import re

import pandas as pd

from config.settings import (
    OPEN_TARGET_COLUMNS,
    POINT_IN_TIME_UNSAFE_FEATURE_COLUMNS,
)

FUTURE_TARGET_PATTERN = re.compile(r"^next_\d+_day_")


def infer_feature_columns(
    frame: pd.DataFrame,
    target_col: str,
) -> list[str]:
    """Return numeric model inputs while blocking future and unsafe columns."""

    columns: list[str] = []
    for column in frame.columns:
        if column == target_col or column in OPEN_TARGET_COLUMNS:
            continue
        if FUTURE_TARGET_PATTERN.match(column):
            continue
        if column in POINT_IN_TIME_UNSAFE_FEATURE_COLUMNS:
            continue
        if pd.api.types.is_numeric_dtype(frame[column]):
            columns.append(column)
    return columns

__all__ = [
    "FUTURE_TARGET_PATTERN",
    "infer_feature_columns",
]
