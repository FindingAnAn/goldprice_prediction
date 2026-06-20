import pandas as pd

from src.pipelines import ingestion


def test_ingestion_pipeline_truncates_before_api_calls(monkeypatch):
    events: list[str] = []

    monkeypatch.setattr(
        ingestion,
        "prepare_database_schema",
        lambda: events.append("schema"),
    )
    monkeypatch.setattr(
        ingestion,
        "truncate_pipeline_data",
        lambda: events.append("truncate"),
    )
    monkeypatch.setattr(
        ingestion,
        "ingest_raw_sources",
        lambda start, end: (
            events.append("ingest") or (1, {}, {}, {}, {}, 0)
        ),
    )
    monkeypatch.setattr(
        ingestion,
        "populate_staging_daily_master",
        lambda: events.append("staging") or 1,
    )
    monkeypatch.setattr(
        ingestion,
        "run_cleaning",
        lambda max_gap_days, z_threshold: events.append("cleaning"),
    )
    monkeypatch.setattr(
        ingestion,
        "run_feature_engineering",
        lambda: events.append("features") or {},
    )
    empty = pd.DataFrame()
    monkeypatch.setattr(ingestion, "load_master_feature_sample", lambda: empty)
    monkeypatch.setattr(ingestion, "load_target_label_sample", lambda: empty)
    monkeypatch.setattr(ingestion, "render_ingestion_report", lambda report: None)
    monkeypatch.setattr(
        ingestion,
        "validate_ingestion_report",
        lambda report: events.append("validate"),
    )

    ingestion.run_ingestion_pipeline(start="2010-01-01", end=None)

    assert events[:3] == ["schema", "truncate", "ingest"]


def test_ingestion_can_skip_schema_when_caller_already_started_run(monkeypatch):
    events: list[str] = []
    monkeypatch.setattr(
        ingestion,
        "prepare_database_schema",
        lambda: events.append("schema"),
    )
    monkeypatch.setattr(
        ingestion,
        "truncate_pipeline_data",
        lambda: events.append("truncate"),
    )
    monkeypatch.setattr(
        ingestion,
        "ingest_raw_sources",
        lambda start, end: (1, {"GC=F": 1}, {"DFII10": 1, "USEPUINDXD": 1}, {}, {}, 1),
    )
    monkeypatch.setattr(ingestion, "populate_staging_daily_master", lambda: 1000)
    monkeypatch.setattr(ingestion, "run_cleaning", lambda **kwargs: None)
    monkeypatch.setattr(
        ingestion,
        "run_feature_engineering",
        lambda: {"master_features": 1000, "target_labels": 1000},
    )
    monkeypatch.setattr(ingestion, "load_master_feature_sample", pd.DataFrame)
    monkeypatch.setattr(ingestion, "load_target_label_sample", pd.DataFrame)
    monkeypatch.setattr(ingestion, "render_ingestion_report", lambda report: None)

    ingestion.run_ingestion_pipeline(
        prepare_schema=False,
        full_refresh=True,
    )

    assert "schema" not in events
    assert events == ["truncate"]
