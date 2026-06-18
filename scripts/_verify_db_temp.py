from sqlalchemy import text

from src.data.storage.postgres_client import get_engine


queries = {
    "gold_by_source": """
        SELECT source, COUNT(*), MIN(date), MAX(date)
        FROM raw.gold_prices GROUP BY source ORDER BY source
    """,
    "yfinance_by_ticker": """
        SELECT ticker, COUNT(*), MIN(date), MAX(date)
        FROM raw.yfinance_daily GROUP BY ticker ORDER BY ticker
    """,
    "fred_daily_by_series": """
        SELECT series_id, COUNT(*), MIN(date), MAX(date)
        FROM raw.fred_daily GROUP BY series_id ORDER BY series_id
    """,
    "fred_monthly_by_series": """
        SELECT series_id, COUNT(*), MIN(date), MAX(date)
        FROM raw.fred_monthly GROUP BY series_id ORDER BY series_id
    """,
    "eia_by_series": """
        SELECT series_id, COUNT(*), MIN(date), MAX(date)
        FROM raw.eia_oil GROUP BY series_id ORDER BY series_id
    """,
    "pipeline_tables": """
        SELECT 'staging.daily_master', COUNT(*), MIN(date), MAX(date)
        FROM staging.daily_master
        UNION ALL
        SELECT 'features.master_features', COUNT(*), MIN(date), MAX(date)
        FROM features.master_features
        UNION ALL
        SELECT 'features.target_labels', COUNT(*), MIN(date), MAX(date)
        FROM features.target_labels
        UNION ALL
        SELECT 'target_t7_available', COUNT(*), MIN(date), MAX(date)
        FROM features.target_labels
        WHERE next_7_day_price IS NOT NULL
    """,
}

with get_engine().connect() as connection:
    for name, query in queries.items():
        print(f"=== {name} ===")
        for row in connection.execute(text(query)):
            print(*row, sep=" | ")
