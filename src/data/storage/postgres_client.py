"""
src/data/storage/postgres_client.py
=====================================
PostgreSQL helper: kết nối, upsert DataFrame, chạy SQL files.

Functions:
    get_engine              : Tạo SQLAlchemy engine từ .env
    ensure_schemas          : Tạo các schema raw/staging/features nếu chưa có
    upsert_dataframe        : Bulk upsert DataFrame vào PG với ON CONFLICT DO UPDATE
    execute_sql_file        : Chạy một file .sql qua psycopg2
    raw_table_needs_update  : Kiểm tra raw table có cần ingest lại hôm nay không
    run_schema_pipeline     : Chạy tất cả sql/schema/*.sql theo thứ tự
    run_feature_pipeline    : Chạy tất cả sql/features/*.sql theo thứ tự
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Sequence

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from psycopg2 import sql
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config.settings import DatabaseConfig
from src.utils.config_loader import (
    SQL_DIR,
    PG_SCHEMA_RAW,
    PG_SCHEMA_STAGING,
    PG_SCHEMA_FEATURES,
    PG_SCHEMA_FORECASTING,
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)
SCHEMA_SQL_ORDER = (
    "01_raw_tables.sql",
    "02_staging_tables.sql",
    "03_feature_tables.sql",
    "04_forecasting_tables.sql",
)
FEATURE_SQL_ORDER = (
    "01_price_features.sql",
    "02_momentum_features.sql",
    "03_trend_features.sql",
    "04_macro_features.sql",
    "05_ratio_features.sql",
    "06_target_labels.sql",
    "07_sliding_window.sql",
    "09_ewma_features.sql",
    "10_seasonality_features.sql",
    "11_market_driver_features.sql",
    "08_master_features.sql",
)


def _prepare_dataframe_for_upsert(df: pd.DataFrame) -> pd.DataFrame:
    """Return a SQL-ready frame without accidental index columns."""

    prepared = df.copy()
    if prepared.index.name is None:
        return prepared.reset_index(drop=True)
    return prepared.reset_index(drop=False)


# ─────────────────────────────────────────────────────────────────────────────
# 1. ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def get_engine() -> Engine:
    """Tạo SQLAlchemy engine từ ``DatabaseConfig``.

    Config được đọc tập trung từ ``config.settings.DatabaseConfig.from_env()``
    thay vì gọi ``os.getenv()`` rải rác (Luật 2.1).

    Returns:
        sqlalchemy.engine.Engine kết nối tới PostgreSQL.
    """
    db_config = DatabaseConfig.from_env()
    engine = create_engine(
        db_config.sqlalchemy_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    logger.info(
        "PG engine created",
        extra={"host": db_config.host, "port": db_config.port, "db": db_config.dbname},
    )
    return engine


def get_connection_params() -> dict:
    """Trả về dict params cho ``psycopg2.connect()``.

    Đọc từ ``DatabaseConfig.from_env()`` để tập trung quản lý config.

    Returns:
        Dict với keys: host, port, user, password, dbname.
    """
    return DatabaseConfig.from_env().to_psycopg2_params()


# ─────────────────────────────────────────────────────────────────────────────
# 2. UPSERT DATAFRAME
# ─────────────────────────────────────────────────────────────────────────────

def upsert_dataframe(
    df: pd.DataFrame,
    table: str,
    schema: str,
    conflict_cols: Sequence[str],
    engine: Engine | None = None,
) -> int:
    """Bulk upsert DataFrame vào PostgreSQL với ON CONFLICT DO UPDATE.

    Các cột trong `conflict_cols` tạo thành composite key để detect trùng lặp.
    Các cột còn lại sẽ được UPDATE nếu có conflict. Cột `ingested_at` luôn
    được cập nhật khi có conflict.

    Args:
        df            : DataFrame cần upsert. Index không được dùng (reset trước).
        table         : Tên bảng (không kèm schema).
        schema        : Schema PostgreSQL (ví dụ: 'raw', 'staging').
        conflict_cols : Danh sách cột tạo conflict key.
        engine        : Giữ để tương thích API cũ; bulk upsert dùng psycopg2.

    Returns:
        Số dòng được upsert.

    Raises:
        psycopg2.Error: Nếu lỗi database.
    """
    if df is None or df.empty:
        logger.warning("upsert_dataframe: DataFrame rỗng, bỏ qua.", extra={"table": f"{schema}.{table}"})
        return 0

    df = _prepare_dataframe_for_upsert(df)

    cols = list(df.columns)
    update_cols = [c for c in cols if c not in conflict_cols]

    full_table = f'"{schema}"."{table}"'
    conflict_clause = ", ".join(f'"{c}"' for c in conflict_cols)
    col_clause     = ", ".join(f'"{c}"' for c in cols)
    placeholder    = "(" + ", ".join(["%s"] * len(cols)) + ")"

    if update_cols:
        update_clause = ", ".join(
            f'"{c}" = EXCLUDED."{c}"' for c in update_cols
        )
        if "updated_at" not in cols:
            update_clause = f"{update_clause}, updated_at = NOW()"
        sql = (
            f"INSERT INTO {full_table} ({col_clause}) VALUES %s "
            f"ON CONFLICT ({conflict_clause}) DO UPDATE SET {update_clause}"
        )
    else:
        sql = (
            f"INSERT INTO {full_table} ({col_clause}) VALUES %s "
            f"ON CONFLICT ({conflict_clause}) DO NOTHING"
        )

    rows = [tuple(row) for row in df.itertuples(index=False, name=None)]

    conn_params = get_connection_params()
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            execute_values(cur, sql, rows, template=None, page_size=1000)
        conn.commit()

    logger.info(
        "Upsert hoàn tất",
        extra={"table": f"{schema}.{table}", "rows": len(rows)},
    )
    return len(rows)


# ─────────────────────────────────────────────────────────────────────────────
# 3. EXECUTE SQL FILE
# ─────────────────────────────────────────────────────────────────────────────

def ensure_schemas() -> None:
    """Tạo các schema raw, staging, features nếu chưa tồn tại.

    Dùng autocommit=True vì CREATE SCHEMA không thể chạy trong transaction block
    trên một số cấu hình PostgreSQL.
    """
    schemas = [
        PG_SCHEMA_RAW,
        PG_SCHEMA_STAGING,
        PG_SCHEMA_FEATURES,
        PG_SCHEMA_FORECASTING,
    ]
    conn_params = get_connection_params()
    with psycopg2.connect(**conn_params) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            for schema in schemas:
                cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
                logger.info("Schema ensured", extra={"schema": schema})


def truncate_pipeline_data() -> dict[str, int]:
    """Truncate raw, staging and feature data while preserving run history.

    The forecasting schema is deliberately excluded so experiment metrics,
    predictions and logs remain auditable across full data refreshes.
    """

    refresh_schemas = (
        PG_SCHEMA_FEATURES,
        PG_SCHEMA_STAGING,
        PG_SCHEMA_RAW,
    )
    conn_params = get_connection_params()
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_type = 'BASE TABLE'
                  AND table_schema = ANY(%s)
                ORDER BY
                    CASE table_schema
                        WHEN 'features' THEN 1
                        WHEN 'staging' THEN 2
                        WHEN 'raw' THEN 3
                    END,
                    table_name
                """,
                (list(refresh_schemas),),
            )
            tables = cursor.fetchall()
            if tables:
                identifiers = [
                    sql.Identifier(schema_name, table_name)
                    for schema_name, table_name in tables
                ]
                cursor.execute(
                    sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(
                        sql.SQL(", ").join(identifiers)
                    )
                )
        conn.commit()

    counts = {
        schema_name: sum(1 for schema, _ in tables if schema == schema_name)
        for schema_name in refresh_schemas
    }
    logger.info(
        "Pipeline data truncated",
        extra={
            "schemas": list(refresh_schemas),
            "table_counts": counts,
            "forecasting_preserved": True,
        },
    )
    return counts


def execute_sql_file(path: str | Path) -> None:
    """Chạy một file .sql qua psycopg2.

    - DDL statements (CREATE, DROP, ALTER) dùng autocommit=True từng câu.
    - DML statements (INSERT, UPDATE, DELETE, SELECT) chạy trong transaction.
    - Bỏ qua statements rỗng hoặc chỉ có comment.
    - Bỏ qua các lệnh psql client (\\i, \\c, ...).

    Args:
        path: Đường dẫn tuyệt đối đến file .sql.

    Raises:
        FileNotFoundError : Nếu file không tồn tại.
        psycopg2.Error    : Nếu lỗi SQL execution.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"SQL file không tìm thấy: {path}")

    sql_text = path.read_text(encoding="utf-8")

    # Remove full-line SQL comments before splitting. A semicolon inside a
    # comment must not terminate the preceding SQL statement.
    executable_lines = [
        line.split("--", 1)[0]
        for line in sql_text.splitlines()
        if not line.lstrip().startswith("--")
    ]
    executable_sql = "\n".join(executable_lines)

    # Tách statements theo `;`, bỏ qua rỗng/psql client commands
    raw_stmts = executable_sql.split(";")
    statements = []
    for s in raw_stmts:
        s = s.strip()
        if not s:
            continue
        # Bỏ qua comment-only và psql client commands (\i, \c, ...)
        lines = [l for l in s.splitlines() if l.strip() and not l.strip().startswith("--")]
        if not lines:
            continue
        first_word = lines[0].strip()
        if first_word.startswith("\\"):
            continue
        statements.append(s)

    # DDL keywords cần autocommit
    DDL_KEYWORDS = ("CREATE", "DROP", "ALTER", "TRUNCATE")

    conn_params = get_connection_params()
    conn = psycopg2.connect(**conn_params)
    try:
        for stmt in statements:
            first_keyword = stmt.strip().split()[0].upper() if stmt.strip() else ""
            is_ddl = first_keyword in DDL_KEYWORDS

            if is_ddl:
                conn.autocommit = True
            else:
                conn.autocommit = False

            with conn.cursor() as cur:
                try:
                    cur.execute(stmt)
                    if not is_ddl:
                        conn.commit()
                except psycopg2.Error as e:
                    if not conn.autocommit:
                        conn.rollback()
                    logger.error(
                        "SQL execution error",
                        extra={"file": path.name, "stmt_preview": stmt[:120], "error": str(e)},
                    )
                    raise
    finally:
        conn.close()

    logger.info("SQL file executed", extra={"file": path.name, "statements": len(statements)})


# ─────────────────────────────────────────────────────────────────────────────
# 4. RAW TABLE FRESHNESS CHECK
# ─────────────────────────────────────────────────────────────────────────────

def raw_table_needs_update(schema: str, table: str) -> bool:
    """Kiểm tra xem raw table có cần ingest lại hôm nay không.

    Logic:
    - Nếu bảng chưa tồn tại → cần update (True).
    - Nếu bảng trống → cần update (True).
    - Nếu MAX(updated_at) cùng ngày hôm nay → bỏ qua (False).
    - Nếu MAX(updated_at) khác ngày hôm nay → cần update (True).

    Chỉ áp dụng cho bảng raw (raw.gold_prices, raw.yfinance_daily, ...).
    Bảng staging và features luôn được xử lý lại (trả về True).

    Args:
        schema: Schema name.
        table : Table name.

    Returns:
        True nếu cần ingest/update, False nếu đã cập nhật hôm nay.
    """
    if not table_exists(schema, table):
        logger.info("Table not found, needs creation", extra={"schema": schema, "table": table})
        return True

    engine = get_engine()
    with engine.connect() as conn:
        # Kiểm tra bảng có cột updated_at không
        has_col = conn.execute(text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.columns "
            "  WHERE table_schema = :schema AND table_name = :table "
            "  AND column_name = 'updated_at'"
            ")"
        ), {"schema": schema, "table": table}).scalar()

        if not has_col:
            logger.info("Table has no updated_at column", extra={"schema": schema, "table": table})
            return True

        result = conn.execute(
            text(f'SELECT COUNT(*), MAX(updated_at) FROM "{schema}"."{table}"')
        ).fetchone()

        row_count, last_updated = result
        if row_count == 0:
            logger.info("Table is empty, needs ingest", extra={"schema": schema, "table": table})
            return True

        today = date.today()
        if last_updated is None:
            return True

        last_date = last_updated.date() if hasattr(last_updated, 'date') else last_updated
        if last_date >= today:
            logger.info("Table already ingested today, skipping", extra={"schema": schema, "table": table, "last_date": str(last_date)})
            return False
        else:
            logger.info("Table needs re-ingest", extra={"schema": schema, "table": table, "last_date": str(last_date), "today": str(today)})
            return True


# ─────────────────────────────────────────────────────────────────────────────
# 5. PIPELINE RUNNERS
# ─────────────────────────────────────────────────────────────────────────────

def run_schema_pipeline(sql_dir: Path = SQL_DIR) -> None:
    """Tạo schemas trước, sau đó chạy tất cả files trong sql/schema/ theo thứ tự.

    Bước 1: ensure_schemas() — tạo raw/staging/features schema bằng autocommit.
    Bước 2: Chạy từng .sql file (01_raw_tables, 02_staging_tables, 03_feature_tables).

    Args:
        sql_dir: Root của thư mục sql/ (mặc định từ config).
    """
    # Đảm bảo schemas tồn tại trước khi chạy DDL
    ensure_schemas()

    schema_dir = sql_dir / "schema"
    _run_ordered_sql_dir(
        schema_dir,
        label="schema",
        ordered_names=SCHEMA_SQL_ORDER,
    )


def run_feature_pipeline(sql_dir: Path = SQL_DIR) -> None:
    """Chạy tất cả files trong sql/features/ theo thứ tự số prefix.

    Args:
        sql_dir: Root của thư mục sql/ (mặc định từ config).
    """
    features_dir = sql_dir / "features"
    _run_ordered_sql_dir(
        features_dir,
        label="features",
        ordered_names=FEATURE_SQL_ORDER,
    )


def _run_ordered_sql_dir(
    directory: Path,
    label: str,
    ordered_names: Sequence[str] | None = None,
) -> None:
    """Chạy tất cả .sql files trong directory theo thứ tự tên file."""
    if not directory.exists():
        raise FileNotFoundError(f"SQL directory không tìm thấy: {directory}")

    if ordered_names is None:
        sql_files = sorted(directory.glob("*.sql"))
    else:
        sql_files = [directory / name for name in ordered_names]
        missing_files = [path.name for path in sql_files if not path.exists()]
        if missing_files:
            raise FileNotFoundError(
                f"Missing ordered SQL files in {directory}: {missing_files}"
            )
    if not sql_files:
        logger.warning("Không tìm thấy .sql file nào", extra={"dir": str(directory)})
        return

    logger.info(
        "SQL pipeline started",
        extra={"label": label, "file_count": len(sql_files)},
    )

    for i, sql_file in enumerate(sql_files, 1):
        logger.info(
            "Executing SQL file",
            extra={"label": label, "step": f"{i}/{len(sql_files)}", "file": sql_file.name},
        )
        execute_sql_file(sql_file)

    logger.info("SQL pipeline completed", extra={"label": label, "total": len(sql_files)})


def table_exists(schema: str, table: str) -> bool:
    """Kiểm tra bảng có tồn tại trong PostgreSQL không.

    Args:
        schema: Schema name.
        table : Table name.

    Returns:
        True nếu bảng tồn tại.
    """
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT EXISTS ("
                "  SELECT 1 FROM information_schema.tables "
                "  WHERE table_schema = :schema AND table_name = :table"
                ")"
            ),
            {"schema": schema, "table": table},
        )
        return bool(result.scalar())


def get_row_count(schema: str, table: str) -> int:
    """Trả về số dòng trong một bảng PostgreSQL.

    Args:
        schema: Schema name.
        table : Table name.

    Returns:
        Số dòng (int), hoặc -1 nếu bảng không tồn tại.
    """
    engine = get_engine()
    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT to_regclass(:qualified_name) IS NOT NULL"),
            {"qualified_name": f"{schema}.{table}"},
        ).scalar()
        if not exists:
            return -1
        result = conn.execute(text(f'SELECT COUNT(*) FROM "{schema}"."{table}"'))
        return int(result.scalar())  # type: ignore


def get_row_counts(schema: str, tables: Sequence[str]) -> dict[str, int]:
    """Return counts for multiple trusted table names over one connection."""

    engine = get_engine()
    counts: dict[str, int] = {}
    with engine.connect() as connection:
        for table in tables:
            exists = connection.execute(
                text("SELECT to_regclass(:qualified_name) IS NOT NULL"),
                {"qualified_name": f"{schema}.{table}"},
            ).scalar()
            counts[table] = (
                int(
                    connection.execute(
                        text(f'SELECT COUNT(*) FROM "{schema}"."{table}"')
                    ).scalar()
                )
                if exists
                else -1
            )
    return counts
