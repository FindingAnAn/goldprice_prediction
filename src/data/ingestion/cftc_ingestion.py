"""Ingest point-in-time-safe CFTC gold positioning data."""

from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import requests

from src.data.storage.postgres_client import upsert_dataframe
from src.utils.config_loader import (
    CFTC_CURRENT_URL,
    CFTC_FIRST_DISAGGREGATED_YEAR,
    CFTC_GOLD_CONTRACT_CODE,
    CFTC_HISTORY_URL_TEMPLATE,
    CFTC_PATH,
    DATA_END_DATE,
    DATA_START_DATE,
    PG_SCHEMA_RAW,
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

_SOURCE_COLUMNS = {
    "Market_and_Exchange_Names": "market_name",
    "Report_Date_as_YYYY-MM-DD": "report_date",
    "CFTC_Contract_Market_Code": "contract_code",
    "Open_Interest_All": "open_interest",
    "Prod_Merc_Positions_Long_All": "producer_long",
    "Prod_Merc_Positions_Short_All": "producer_short",
    "Swap_Positions_Long_All": "swap_long",
    "Swap__Positions_Short_All": "swap_short",
    "M_Money_Positions_Long_All": "managed_money_long",
    "M_Money_Positions_Short_All": "managed_money_short",
    "M_Money_Positions_Spread_All": "managed_money_spread",
    "Change_in_M_Money_Long_All": "managed_money_long_change",
    "Change_in_M_Money_Short_All": "managed_money_short_change",
}

_CURRENT_COLUMN_POSITIONS = {
    0: "Market_and_Exchange_Names",
    2: "Report_Date_as_YYYY-MM-DD",
    3: "CFTC_Contract_Market_Code",
    7: "Open_Interest_All",
    8: "Prod_Merc_Positions_Long_All",
    9: "Prod_Merc_Positions_Short_All",
    10: "Swap_Positions_Long_All",
    11: "Swap__Positions_Short_All",
    13: "M_Money_Positions_Long_All",
    14: "M_Money_Positions_Short_All",
    15: "M_Money_Positions_Spread_All",
    61: "Change_in_M_Money_Long_All",
    62: "Change_in_M_Money_Short_All",
}


def _archive_path(year: int, cache_dir: Path = CFTC_PATH) -> Path:
    return cache_dir / f"fut_disagg_txt_{year}.zip"


def _load_archive_bytes(
    year: int,
    cache_dir: Path = CFTC_PATH,
    session: requests.Session | None = None,
) -> bytes:
    """Load an immutable historical archive from cache or CFTC."""

    path = _archive_path(year, cache_dir)
    is_closed_year = year < date.today().year
    if is_closed_year and path.exists():
        return path.read_bytes()

    client = session or requests.Session()
    url = CFTC_HISTORY_URL_TEMPLATE.format(year=year)
    response = client.get(
        url,
        timeout=60,
        headers={"User-Agent": "goldprice-prediction-research/1.0"},
    )
    response.raise_for_status()
    cache_dir.mkdir(parents=True, exist_ok=True)
    path.write_bytes(response.content)
    return response.content


def parse_cftc_gold_archive(
    payload: bytes,
    contract_code: str = CFTC_GOLD_CONTRACT_CODE,
) -> pd.DataFrame:
    """Extract COMEX gold rows from an annual ZIP archive."""

    with ZipFile(BytesIO(payload)) as archive:
        member = archive.namelist()[0]
        frame = pd.read_csv(
            archive.open(member),
            dtype={"CFTC_Contract_Market_Code": "string"},
            low_memory=False,
        )
    return parse_cftc_gold_frame(frame, contract_code=contract_code)


def parse_cftc_gold_current(
    payload: bytes,
    contract_code: str = CFTC_GOLD_CONTRACT_CODE,
) -> pd.DataFrame:
    """Extract COMEX gold rows from the current plain-text report."""

    frame = pd.read_csv(
        BytesIO(payload),
        header=None,
        usecols=list(_CURRENT_COLUMN_POSITIONS),
        low_memory=False,
    )
    frame = frame.rename(columns=_CURRENT_COLUMN_POSITIONS)
    return parse_cftc_gold_frame(frame, contract_code=contract_code)


def parse_cftc_gold_frame(
    frame: pd.DataFrame,
    contract_code: str = CFTC_GOLD_CONTRACT_CODE,
) -> pd.DataFrame:
    """Normalize a report and derive its conservative availability date."""

    frame = frame.copy()
    frame.columns = [str(column).strip() for column in frame.columns]
    if "Report_Date_as_YYYY-MM-DD" not in frame.columns:
        if "As_of_Date_In_Form_YYMMDD" not in frame.columns:
            raise ValueError("CFTC archive has no supported report-date column")
        compact_date = (
            frame["As_of_Date_In_Form_YYMMDD"]
            .astype("string")
            .str.replace(r"\.0$", "", regex=True)
            .str.zfill(6)
        )
        parsed_date = pd.to_datetime(
            compact_date,
            format="%y%m%d",
            errors="coerce",
        ).rename("Report_Date_as_YYYY-MM-DD")
        frame = pd.concat([frame, parsed_date], axis=1)

    missing = set(_SOURCE_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"CFTC archive missing columns: {sorted(missing)}")
    frame = frame[list(_SOURCE_COLUMNS)].rename(columns=_SOURCE_COLUMNS)
    frame["contract_code"] = (
        frame["contract_code"].astype("string").str.strip().str.zfill(6)
    )
    frame = frame[frame["contract_code"] == contract_code].copy()
    frame["report_date"] = pd.to_datetime(
        frame["report_date"],
        errors="coerce",
    )
    # COT positions are dated Tuesday and normally released Friday. Using
    # Friday as available_date prevents Tuesday-to-Thursday look-ahead.
    frame["available_date"] = frame["report_date"] + pd.Timedelta(days=3)

    numeric_columns = [
        column
        for column in _SOURCE_COLUMNS.values()
        if column not in {"market_name", "report_date", "contract_code"}
    ]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame = frame.dropna(
        subset=["report_date", "available_date", "open_interest"],
    )
    frame["report_date"] = frame["report_date"].dt.date
    frame["available_date"] = frame["available_date"].dt.date
    return (
        frame[
            [
                "report_date",
                "available_date",
                "contract_code",
                "market_name",
                *numeric_columns,
            ]
        ]
        .drop_duplicates(["report_date", "contract_code"], keep="last")
        .sort_values("report_date")
    )


def fetch_cftc_current_positioning(
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Fetch the current weekly CFTC disaggregated futures report."""

    client = session or requests.Session()
    response = client.get(
        CFTC_CURRENT_URL,
        timeout=60,
        headers={"User-Agent": "goldprice-prediction-research/1.0"},
    )
    response.raise_for_status()
    return parse_cftc_gold_current(response.content)


def fetch_cftc_gold_positioning(
    start: str = DATA_START_DATE,
    end: str | None = DATA_END_DATE,
    cache_dir: Path = CFTC_PATH,
) -> pd.DataFrame:
    """Fetch annual archives and append the freshest current report."""

    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end) if end else date.today()
    first_year = max(CFTC_FIRST_DISAGGREGATED_YEAR, start_date.year)
    frames: list[pd.DataFrame] = []
    with requests.Session() as session:
        for year in range(first_year, end_date.year + 1):
            try:
                payload = _load_archive_bytes(year, cache_dir, session)
                frames.append(parse_cftc_gold_archive(payload))
            except Exception:
                logger.exception(
                    "CFTC archive ingestion failed",
                    extra={"source": "cftc", "year": year},
                )
        try:
            frames.append(fetch_cftc_current_positioning(session))
        except Exception:
            logger.exception(
                "Current CFTC report ingestion failed",
                extra={"source": "cftc", "url": CFTC_CURRENT_URL},
            )

    if not frames:
        return pd.DataFrame()
    result = (
        pd.concat(frames, ignore_index=True)
        .drop_duplicates(
            ["report_date", "contract_code"],
            keep="last",
        )
        .sort_values("report_date")
    )
    return result[
        (pd.to_datetime(result["report_date"]).dt.date >= start_date)
        & (pd.to_datetime(result["available_date"]).dt.date <= end_date)
    ].reset_index(drop=True)


def ingest_cftc_gold_positioning(
    start: str = DATA_START_DATE,
    end: str | None = DATA_END_DATE,
) -> int:
    """Fetch and upsert CFTC gold positioning observations."""

    frame = fetch_cftc_gold_positioning(start=start, end=end)
    if frame.empty:
        logger.warning("CFTC gold positioning returned no rows")
        return 0
    rows = upsert_dataframe(
        frame,
        table="cftc_gold_positioning",
        schema=PG_SCHEMA_RAW,
        conflict_cols=["report_date", "contract_code"],
    )
    logger.info(
        "CFTC gold positioning ingested",
        extra={
            "source": "cftc",
            "rows": rows,
            "latest_available_date": str(frame["available_date"].max()),
        },
    )
    return rows


__all__ = [
    "fetch_cftc_current_positioning",
    "fetch_cftc_gold_positioning",
    "ingest_cftc_gold_positioning",
    "parse_cftc_gold_archive",
    "parse_cftc_gold_current",
    "parse_cftc_gold_frame",
]
