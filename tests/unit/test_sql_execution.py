from __future__ import annotations

from src.data.storage import postgres_client


class _FakeCursor:
    def __init__(self, statements: list[str]):
        self.statements = statements

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, statement: str) -> None:
        self.statements.append(statement)


class _FakeConnection:
    def __init__(self):
        self.autocommit = False
        self.statements: list[str] = []

    def cursor(self):
        return _FakeCursor(self.statements)

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None

    def close(self) -> None:
        return None


def test_execute_sql_file_ignores_semicolon_inside_full_line_comment(
    monkeypatch,
    tmp_path,
):
    sql_file = tmp_path / "schema.sql"
    sql_file.write_text(
        """
        CREATE TABLE test_table (
            value DOUBLE PRECISION,
            other_value DOUBLE PRECISION -- deprecated source; kept for compatibility
        );
        """,
        encoding="utf-8",
    )
    connection = _FakeConnection()
    monkeypatch.setattr(
        postgres_client.psycopg2,
        "connect",
        lambda **kwargs: connection,
    )

    postgres_client.execute_sql_file(sql_file)

    assert len(connection.statements) == 1
    assert "other_value DOUBLE PRECISION" in connection.statements[0]
