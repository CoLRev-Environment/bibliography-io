"""Tests for Excel file APIs using the retained workbook fixture."""

from pathlib import Path

from bibliography_io import load_records
from bibliography_io import write_records


DATA = Path(__file__).parent / "data" / "xlsx"
ORIGINAL_DUPLICATE_FIXTURE = DATA / "load.xlsx"


def test_load_xlsx_fixture() -> None:
    records = load_records(ORIGINAL_DUPLICATE_FIXTURE)
    expected = load_records(DATA / "load_expected.bib")
    assert len(records) == len(expected) == 3
    ids = [record["ID"] for record in records.values()]
    assert ids.count("Id_0001") == 3
    assert list(records) == ["Id_0001", "Id_0001#2", "Id_0001#3"]
    assert all(record["Title"] == "Paper title" for record in records.values())
    for key, record in records.items():
        expected_record = expected[key]
        assert record["ID"] == expected_record["id"]
        assert record["Title"] == expected_record["title"]


def test_xlsx_load_write_round_trip(tmp_path: Path) -> None:
    records = load_records(DATA / "write_expected.bib")
    output = tmp_path / "roundtrip.xlsx"
    write_records(records, output)
    reloaded = load_records(output)
    assert list(reloaded) == ["one", "two"]
    assert reloaded == records
