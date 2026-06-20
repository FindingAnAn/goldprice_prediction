from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd

from src.data.ingestion.cftc_ingestion import (
    fetch_cftc_gold_positioning,
    parse_cftc_gold_archive,
    parse_cftc_gold_current,
)


def _archive_bytes(frame: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("f_year.txt", frame.to_csv(index=False))
    return buffer.getvalue()


def test_cftc_gold_parser_filters_contract_and_lags_availability():
    source = pd.DataFrame(
        [
            {
                "Market_and_Exchange_Names": "GOLD - COMMODITY EXCHANGE INC.",
                "Report_Date_as_YYYY-MM-DD": "2026-06-09",
                "CFTC_Contract_Market_Code": "088691",
                "Open_Interest_All": 1000,
                "Prod_Merc_Positions_Long_All": 100,
                "Prod_Merc_Positions_Short_All": 200,
                "Swap_Positions_Long_All": 150,
                "Swap__Positions_Short_All": 250,
                "M_Money_Positions_Long_All": 400,
                "M_Money_Positions_Short_All": 100,
                "M_Money_Positions_Spread_All": 50,
                "Change_in_M_Money_Long_All": 20,
                "Change_in_M_Money_Short_All": -10,
            },
            {
                "Market_and_Exchange_Names": "SILVER",
                "Report_Date_as_YYYY-MM-DD": "2026-06-09",
                "CFTC_Contract_Market_Code": "084691",
                "Open_Interest_All": 500,
                "Prod_Merc_Positions_Long_All": 1,
                "Prod_Merc_Positions_Short_All": 1,
                "Swap_Positions_Long_All": 1,
                "Swap__Positions_Short_All": 1,
                "M_Money_Positions_Long_All": 1,
                "M_Money_Positions_Short_All": 1,
                "M_Money_Positions_Spread_All": 1,
                "Change_in_M_Money_Long_All": 1,
                "Change_in_M_Money_Short_All": 1,
            },
        ]
    )

    result = parse_cftc_gold_archive(_archive_bytes(source))

    assert len(result) == 1
    assert result.iloc[0]["contract_code"] == "088691"
    assert str(result.iloc[0]["report_date"]) == "2026-06-09"
    assert str(result.iloc[0]["available_date"]) == "2026-06-12"


def test_cftc_gold_parser_accepts_legacy_compact_date_column():
    source = pd.DataFrame(
        [
            {
                "Market_and_Exchange_Names": "GOLD",
                "As_of_Date_In_Form_YYMMDD": 100105,
                "CFTC_Contract_Market_Code": "088691",
                "Open_Interest_All": 1000,
                "Prod_Merc_Positions_Long_All": 100,
                "Prod_Merc_Positions_Short_All": 200,
                "Swap_Positions_Long_All": 150,
                "Swap__Positions_Short_All": 250,
                "M_Money_Positions_Long_All": 400,
                "M_Money_Positions_Short_All": 100,
                "M_Money_Positions_Spread_All": 50,
                "Change_in_M_Money_Long_All": 20,
                "Change_in_M_Money_Short_All": -10,
            }
        ]
    )

    result = parse_cftc_gold_archive(_archive_bytes(source))

    assert str(result.iloc[0]["report_date"]) == "2010-01-05"
    assert str(result.iloc[0]["available_date"]) == "2010-01-08"


def test_current_cftc_parser_uses_same_point_in_time_rules():
    row = [""] * 63
    values = {
        0: "GOLD",
        2: "2026-06-09",
        3: "088691",
        7: 1000,
        8: 100,
        9: 200,
        10: 150,
        11: 250,
        13: 400,
        14: 100,
        15: 50,
        61: 20,
        62: -10,
    }
    for position, value in values.items():
        row[position] = value
    payload = pd.DataFrame([row]).to_csv(
        index=False,
        header=False,
    ).encode()

    result = parse_cftc_gold_current(payload)

    assert len(result) == 1
    assert str(result.iloc[0]["available_date"]) == "2026-06-12"


def test_fetch_deduplicates_current_report_against_annual_archive(
    monkeypatch,
    tmp_path,
):
    source = pd.DataFrame(
        [
            {
                "Market_and_Exchange_Names": "GOLD",
                "Report_Date_as_YYYY-MM-DD": "2026-06-09",
                "CFTC_Contract_Market_Code": "088691",
                "Open_Interest_All": 1000,
                "Prod_Merc_Positions_Long_All": 100,
                "Prod_Merc_Positions_Short_All": 200,
                "Swap_Positions_Long_All": 150,
                "Swap__Positions_Short_All": 250,
                "M_Money_Positions_Long_All": 400,
                "M_Money_Positions_Short_All": 100,
                "M_Money_Positions_Spread_All": 50,
                "Change_in_M_Money_Long_All": 20,
                "Change_in_M_Money_Short_All": -10,
            }
        ]
    )
    archive_payload = _archive_bytes(source)
    current = parse_cftc_gold_archive(archive_payload)
    monkeypatch.setattr(
        "src.data.ingestion.cftc_ingestion._load_archive_bytes",
        lambda year, cache_dir, session: archive_payload,
    )
    monkeypatch.setattr(
        "src.data.ingestion.cftc_ingestion.fetch_cftc_current_positioning",
        lambda session: current,
    )

    result = fetch_cftc_gold_positioning(
        start="2026-01-01",
        end="2026-06-20",
        cache_dir=tmp_path,
    )

    assert len(result) == 1
