"""Tests for Excel file APIs using the retained workbook fixture."""

from pathlib import Path

from bibliography_io import load_raw
from bibliography_io import write


DATA = Path(__file__).parent / "data" / "xlsx"
ORIGINAL_DUPLICATE_FIXTURE = DATA / "load.xlsx"


def test_load_xlsx_fixture() -> None:
    records = load_raw(ORIGINAL_DUPLICATE_FIXTURE)
    expected = load_raw(DATA / "load_expected.bib")
    assert len(records) == len(expected) == 3
    assert all(r["title"] == "Paper title" for r in records)
    assert [r["type"] for r in records] == [
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
    write(records, path=output)
    reloaded = load_raw(output)
    assert [row["title"] for row in reloaded] == ["One", "Two"]
    assert [row["ID"] for row in reloaded] == ["one", "two"]
