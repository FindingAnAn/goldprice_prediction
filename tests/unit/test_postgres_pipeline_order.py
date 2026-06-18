from __future__ import annotations

from src.data.storage import postgres_client


def test_schema_pipeline_does_not_run_staging_population(monkeypatch, tmp_path):
    schema_dir = tmp_path / "schema"
    schema_dir.mkdir()
    for name in postgres_client.SCHEMA_SQL_ORDER:
        (schema_dir / name).write_text("SELECT 1;", encoding="utf-8")
    (schema_dir / "00_populate_staging.sql").write_text("SELECT 1;", encoding="utf-8")

    executed: list[str] = []
    monkeypatch.setattr(postgres_client, "ensure_schemas", lambda: None)
    monkeypatch.setattr(
        postgres_client,
        "execute_sql_file",
        lambda path: executed.append(path.name),
    )

    postgres_client.run_schema_pipeline(tmp_path)

    assert executed == list(postgres_client.SCHEMA_SQL_ORDER)


def test_feature_pipeline_runs_ewma_before_master(monkeypatch, tmp_path):
    feature_dir = tmp_path / "features"
    feature_dir.mkdir()
    for name in postgres_client.FEATURE_SQL_ORDER:
        (feature_dir / name).write_text("SELECT 1;", encoding="utf-8")

    executed: list[str] = []
    monkeypatch.setattr(
        postgres_client,
        "execute_sql_file",
        lambda path: executed.append(path.name),
    )

    postgres_client.run_feature_pipeline(tmp_path)

    assert executed == list(postgres_client.FEATURE_SQL_ORDER)
    assert executed.index("09_ewma_features.sql") < executed.index(
        "08_master_features.sql"
    )
