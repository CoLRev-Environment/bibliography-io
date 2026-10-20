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
    assert list(records) == ["1", "2", "3"]
    assert all(r["title"] == "Paper title" for r in records.values())
    assert [r["type"] for r in records.values()] == [
        "article",
        "inproceedings",
        "techreport",
    ]


def test_xlsx_load_write_round_trip(tmp_path: Path) -> None:
    records = {
        "one": {"ID": "one", "ENTRYTYPE": "article", "title": "One"},
        "two": {"ID": "two", "ENTRYTYPE": "article", "title": "Two"},
    }
    output = tmp_path / "roundtrip.xlsx"
    write_records(records, path=output)
    reloaded = load_records(output)
    assert list(reloaded) == ["1", "2"]
    assert [row["title"] for row in reloaded.values()] == ["One", "Two"]
    assert [row["id"] for row in reloaded.values()] == ["one", "two"]
