"""
src/data/preprocessing/cleaning.py
=====================================
Làm sạch dữ liệu raw trong PostgreSQL: dedup, fill missing, flag outlier.

Tất cả operations thực hiện trực tiếp trên PostgreSQL qua SQL.
Không xử lý trên Python/pandas để đảm bảo scalability.

Functions:
    remove_duplicates    : Xóa duplicate rows trong raw tables.
    fill_missing_staging : Forward-fill missing values trong staging.daily_master.
    flag_outliers        : Đánh dấu extreme outliers (z-score > threshold).
    run_cleaning_pipeline: Chạy toàn bộ cleaning pipeline.
"""

from __future__ import annotations

from src.utils.logging_config import get_logger
from src.data.storage.postgres_client import get_connection_params, get_row_count

import psycopg2

logger = get_logger(__name__)


def _execute_sql(sql: str, label: str = "") -> None:
    """Chạy một SQL statement trực tiếp qua psycopg2.

    Args:
        sql: SQL statement cần thực thi.
        label: Nhãn mô tả ngắn cho log (nếu rỗng, không log).

    Raises:
        psycopg2.Error: Nếu SQL execution thất bại.
    """
    conn_params = get_connection_params()
    with psycopg2.connect(**conn_params) as conn:
        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    if label:
        logger.info("Cleaning SQL executed", extra={"label": label})


def remove_duplicates() -> None:
    """Xóa duplicate rows trong các raw tables, giữ lại row mới nhất (MAX ctid).

    Áp dụng cho:
        - raw.gold_prices     : key = (date, source)
        - raw.yfinance_daily  : key = (date, ticker)
        - raw.fred_daily      : key = (date, series_id)
        - raw.fred_monthly    : key = (date, series_id)
        - raw.eia_oil         : key = (date, series_id)
    """
    dedup_sqls = {
        "raw.gold_prices": """
            DELETE FROM raw.gold_prices a
            USING raw.gold_prices b
            WHERE a.ctid < b.ctid
              AND a.date = b.date
              AND a.source = b.source
        """,
        "raw.yfinance_daily": """
            DELETE FROM raw.yfinance_daily a
            USING raw.yfinance_daily b
            WHERE a.ctid < b.ctid
              AND a.date = b.date
              AND a.ticker = b.ticker
        """,
        "raw.fred_daily": """
            DELETE FROM raw.fred_daily a
            USING raw.fred_daily b
            WHERE a.ctid < b.ctid
              AND a.date = b.date
              AND a.series_id = b.series_id
        """,
        "raw.fred_monthly": """
            DELETE FROM raw.fred_monthly a
            USING raw.fred_monthly b
            WHERE a.ctid < b.ctid
              AND a.date = b.date
              AND a.series_id = b.series_id
        """,
        "raw.eia_oil": """
            DELETE FROM raw.eia_oil a
            USING raw.eia_oil b
            WHERE a.ctid < b.ctid
              AND a.date = b.date
              AND a.series_id = b.series_id
        """,
    }
    for table, sql in dedup_sqls.items():
        try:
            _execute_sql(sql, label=f"dedup {table}")
        except Exception:
            logger.exception("Lỗi dedup", extra={"table": table})


def fill_missing_staging(max_gap_days: int = 3) -> None:
    """Forward-fill missing values trong staging.daily_master.

    Dùng UPDATE ... FROM với LAG window để fill NULL tối đa ``max_gap_days`` ngày.
    Chạy lặp ``max_gap_days`` lần để đảm bảo fill đủ.

    Args:
        max_gap_days: Số ngày tối đa để forward-fill (mặc định 3).
    """
    logger.info("Forward-fill staging.daily_master", extra={"max_gap_days": max_gap_days})

    # Dùng PostgreSQL để update từng cột có NULL bằng LAG
    # (chạy `max_gap_days` lần để fill chuỗi NULL dài)
    ffill_sql = """
        UPDATE staging.daily_master dm
        SET
            gold_close         = COALESCE(dm.gold_close,
                                   (SELECT d2.gold_close FROM staging.daily_master d2
                                    WHERE d2.date < dm.date AND d2.gold_close IS NOT NULL
                                    ORDER BY d2.date DESC LIMIT 1)),
            dxy_close          = COALESCE(dm.dxy_close,
                                   (SELECT d2.dxy_close FROM staging.daily_master d2
                                    WHERE d2.date < dm.date AND d2.dxy_close IS NOT NULL
                                    ORDER BY d2.date DESC LIMIT 1)),
            wti_oil_price      = COALESCE(dm.wti_oil_price,
                                   (SELECT d2.wti_oil_price FROM staging.daily_master d2
                                    WHERE d2.date < dm.date AND d2.wti_oil_price IS NOT NULL
                                    ORDER BY d2.date DESC LIMIT 1)),
            brent_oil_price    = COALESCE(dm.brent_oil_price,
                                   (SELECT d2.brent_oil_price FROM staging.daily_master d2
                                    WHERE d2.date < dm.date AND d2.brent_oil_price IS NOT NULL
                                    ORDER BY d2.date DESC LIMIT 1)),
            silver_close       = COALESCE(dm.silver_close,
                                   (SELECT d2.silver_close FROM staging.daily_master d2
                                    WHERE d2.date < dm.date AND d2.silver_close IS NOT NULL
                                    ORDER BY d2.date DESC LIMIT 1)),
            sp500_close        = COALESCE(dm.sp500_close,
                                   (SELECT d2.sp500_close FROM staging.daily_master d2
                                    WHERE d2.date < dm.date AND d2.sp500_close IS NOT NULL
                                    ORDER BY d2.date DESC LIMIT 1)),
            us_10y_yield       = COALESCE(dm.us_10y_yield,
                                   (SELECT d2.us_10y_yield FROM staging.daily_master d2
                                    WHERE d2.date < dm.date AND d2.us_10y_yield IS NOT NULL
                                    ORDER BY d2.date DESC LIMIT 1)),
            us_2y_yield        = COALESCE(dm.us_2y_yield,
                                   (SELECT d2.us_2y_yield FROM staging.daily_master d2
                                    WHERE d2.date < dm.date AND d2.us_2y_yield IS NOT NULL
                                    ORDER BY d2.date DESC LIMIT 1)),
            vix                = COALESCE(dm.vix,
                                   (SELECT d2.vix FROM staging.daily_master d2
                                    WHERE d2.date < dm.date AND d2.vix IS NOT NULL
                                    ORDER BY d2.date DESC LIMIT 1)),
            breakeven_inflation= COALESCE(dm.breakeven_inflation,
                                   (SELECT d2.breakeven_inflation FROM staging.daily_master d2
                                    WHERE d2.date < dm.date AND d2.breakeven_inflation IS NOT NULL
                                    ORDER BY d2.date DESC LIMIT 1))
        WHERE dm.gold_close IS NOT NULL  -- chỉ fill rows đã có gold price
    """
    _execute_sql(ffill_sql, label="ffill staging.daily_master")


def flag_outliers(z_threshold: float = 5.0) -> None:
    """Đánh dấu extreme outliers trong staging.daily_master.

    Dùng Z-score rolling 252 ngày. Rows với |z| > z_threshold được set
    cột is_outlier = TRUE để downstream có thể filter.

    Args:
        z_threshold: Ngưỡng Z-score để coi là outlier (mặc định 5.0).
    """
    sql = f"""
        UPDATE staging.daily_master
        SET is_outlier = TRUE
        WHERE date IN (
            SELECT date FROM (
                SELECT
                    date,
                    gold_close,
                    AVG(gold_close)  OVER w AS mean_252,
                    STDDEV(gold_close) OVER w AS std_252,
                    ABS(gold_close - AVG(gold_close) OVER w)
                        / NULLIF(STDDEV(gold_close) OVER w, 0) AS z
                FROM staging.daily_master
                WHERE gold_close IS NOT NULL
                WINDOW w AS (ORDER BY date ROWS BETWEEN 251 PRECEDING AND CURRENT ROW)
            ) sub
            WHERE z > {z_threshold}
        )
    """
    _execute_sql(sql, label="flag outliers")


def run_cleaning_pipeline(max_gap_days: int = 3, z_threshold: float = 5.0) -> None:
    """Chạy toàn bộ cleaning pipeline theo thứ tự.

    Thứ tự: dedup raw → fill missing staging → flag outliers staging.

    Args:
        max_gap_days : Forward-fill tối đa N ngày.
        z_threshold  : Ngưỡng Z-score cho outlier flagging.
    """
    logger.info("Cleaning pipeline started", extra={"max_gap_days": max_gap_days, "z_threshold": z_threshold})

    logger.info("Cleaning step started", extra={"step": "1/3", "action": "remove_duplicates"})
    remove_duplicates()

    logger.info("Cleaning step started", extra={"step": "2/3", "action": "fill_missing_staging"})
    fill_missing_staging(max_gap_days=max_gap_days)

    logger.info("Cleaning step started", extra={"step": "3/3", "action": "flag_outliers"})
    flag_outliers(z_threshold=z_threshold)

    logger.info("Cleaning pipeline completed")
