from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from config.settings import DatabaseConfig
from src.data.ingestion import fred_ingestion
from src.data.ingestion.yfinance_ingestion import (
    _exclusive_yfinance_end,
    _latest_complete_market_date,
)
from src.data.storage.postgres_client import _prepare_dataframe_for_upsert


class _FakeResponse:
    text = "observation_date,DGS10\n2026-06-16,4.43\n"

    def raise_for_status(self) -> None:
        return None


def test_prepare_dataframe_for_upsert_does_not_add_range_index_column():
    frame = pd.DataFrame({"date": ["2026-06-18"], "value": [1.0]})

    prepared = _prepare_dataframe_for_upsert(frame)

    assert list(prepared.columns) == ["date", "value"]


def test_prepare_dataframe_for_upsert_drops_filtered_unnamed_index():
    frame = pd.DataFrame(
        {"date": ["2026-06-16", "2026-06-17"], "value": [1.0, 2.0]}
    ).iloc[[1]]

    prepared = _prepare_dataframe_for_upsert(frame)

    assert list(prepared.columns) == ["date", "value"]


def test_prepare_dataframe_for_upsert_preserves_named_date_index():
    frame = pd.DataFrame(
        {"value": [1.0]},
        index=pd.Index(["2026-06-18"], name="date"),
    )

    prepared = _prepare_dataframe_for_upsert(frame)

    assert list(prepared.columns) == ["date", "value"]


def test_yfinance_end_date_is_inclusive_for_project_callers():
    assert _exclusive_yfinance_end("2026-06-18") == "2026-06-19"


def test_yfinance_excludes_current_session_before_us_close():
    before_close = datetime(2026, 6, 19, 16, 0, tzinfo=timezone.utc)

    assert _latest_complete_market_date(before_close).isoformat() == "2026-06-18"
    assert _exclusive_yfinance_end(None, now=before_close) == "2026-06-19"


def test_yfinance_includes_current_session_after_safe_close():
    after_close = datetime(2026, 6, 20, 0, 0, tzinfo=timezone.utc)

    assert _latest_complete_market_date(after_close).isoformat() == "2026-06-19"
    assert _exclusive_yfinance_end(None, now=after_close) == "2026-06-20"


def test_fred_uses_public_csv_when_api_key_is_missing(monkeypatch):
    monkeypatch.setattr(fred_ingestion, "FRED_KEY_VALID", False)
    monkeypatch.setattr(
        fred_ingestion.requests,
        "get",
        lambda *args, **kwargs: _FakeResponse(),
    )

    frame = fred_ingestion.fetch_fred_series(
        "DGS10",
        api_key="",
        start="2026-06-01",
    )

    assert frame["date"].max().isoformat() == "2026-06-16"
    assert frame["value"].iloc[-1] == 4.43


def test_database_config_accepts_legacy_pg_environment_names(monkeypatch):
    for key in ("DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("PG_HOST", "db.local")
    monkeypatch.setenv("PG_PORT", "5433")
    monkeypatch.setenv("PG_USER", "gold_user")
    monkeypatch.setenv("PG_PASSWORD", "secret")
    monkeypatch.setenv("PG_DB", "gold_db")

    config = DatabaseConfig.from_env()

    assert config.host == "db.local"
    assert config.port == 5433
    assert config.user == "gold_user"
    assert config.password == "secret"
    assert config.dbname == "gold_db"
