"""Shared leakage-safe utilities for time-series modeling."""

from __future__ import annotations

import re

import pandas as pd

from config.settings import (
    OPEN_TARGET_COLUMNS,
    POINT_IN_TIME_UNSAFE_FEATURE_COLUMNS,
)

FUTURE_TARGET_PATTERN = re.compile(r"^next_\d+_day_")


def time_series_train_test_split(
    frame: pd.DataFrame,
    test_size: float = 0.2,
    gap: int = 0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Chronologically split a frame and purge rows between train and test."""

    if frame.empty:
        raise ValueError("Cannot split an empty DataFrame")
    if not 0 < test_size < 1:
        raise ValueError("test_size must be between 0 and 1")
    if gap < 0:
        raise ValueError("gap must be non-negative")

    split_index = min(
        max(1, int(len(frame) * (1 - test_size))),
        len(frame) - 1,
    )
    train_end = split_index - gap
    if train_end < 1:
        raise ValueError(
            f"Not enough rows ({len(frame)}) for test_size={test_size} "
            f"and gap={gap}"
        )
    return frame.iloc[:train_end].copy(), frame.iloc[split_index:].copy()


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


def validate_feature_columns(feature_columns: list[str]) -> None:
    """Fail fast when future labels or point-in-time-unsafe fields are inputs."""

    unsafe = [
        column
        for column in feature_columns
        if (
            column in OPEN_TARGET_COLUMNS
            or FUTURE_TARGET_PATTERN.match(column)
            or column in POINT_IN_TIME_UNSAFE_FEATURE_COLUMNS
        )
    ]
    if unsafe:
        raise ValueError(
            "Leakage-prone columns cannot be model features: "
            f"{sorted(unsafe)}"
        )


__all__ = [
    "FUTURE_TARGET_PATTERN",
    "infer_feature_columns",
    "time_series_train_test_split",
    "validate_feature_columns",
]
