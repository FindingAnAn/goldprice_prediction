from __future__ import annotations

import pytest

from src.data.preprocessing.cleaning import fill_missing_staging


def test_fill_missing_staging_rejects_negative_gap():
    with pytest.raises(ValueError, match="max_gap_days"):
        fill_missing_staging(max_gap_days=-1)
