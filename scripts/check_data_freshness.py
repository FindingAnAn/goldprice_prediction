"""Print latest available and stored dates for every configured source."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.ingestion.freshness import (
    collect_api_freshness,
    collect_database_freshness,
)


def _render(records: list[object]) -> None:
    for record in records:
        latest = record.latest_date.isoformat() if record.latest_date else "-"
        print(
            f"{record.source:15} {record.item:28} "
            f"latest={latest:10} status={record.status}"
        )
        if record.detail:
            print(f"  {record.detail}")


if __name__ == "__main__":
    print("=== API freshness ===")
    _render(collect_api_freshness())
    print("\n=== PostgreSQL freshness ===")
    _render(collect_database_freshness())
