"""Tests for CSV file APIs using the retained CSV fixture."""

from pathlib import Path

from bibliography_io import dumps
from bibliography_io import load_records
from bibliography_io import loads
from bibliography_io import write_records


DATA = Path(__file__).parent / "data" / "csv"


def test_load_csv_fixture() -> None:
    records = load_records(DATA / "load.csv")
    expected = load_records(DATA / "load_expected.bib")
    assert len(records) == len(expected)
    for record, expected_record in zip(records.values(), expected.values()):
        assert record["Title"] == expected_record["title"]
        assert record["DOI"] == expected_record["doi"]


def test_csv_load_write_round_trip(tmp_path: Path) -> None:
    records = load_records(DATA / "write_expected.bib")
    text = dumps(records, format="csv")
    output = tmp_path / "roundtrip.csv"
    write_records(records, output)

    assert loads(text, format="csv") == records
    assert load_records(output) == records
    assert output.read_text(encoding="utf-8") == (
        DATA / "write_expected.csv"
    ).read_text(encoding="utf-8")


def test_csv_fixture_writes_and_reloads(tmp_path: Path) -> None:
    records = load_records(DATA / "load.csv")
    output = tmp_path / "fixture-roundtrip.csv"
    write_records(records, output)
    assert load_records(output) == records
