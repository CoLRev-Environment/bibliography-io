"""Tests for NBIB loading using the retained fixture."""

from pathlib import Path

from bibliography_io import dumps
from bibliography_io import load_records
from bibliography_io import write_records


DATA = Path(__file__).parent / "data" / "nbib"


def test_load_nbib_fixture() -> None:
    records = load_records(DATA / "load.nbib")
    expected = load_records(DATA / "load_expected.bib")
    record = next(iter(records))
    expected_record = next(iter(expected))
    assert record.get("ID") is None
    for field, value in expected_record.items():
        if field != "ID":
            assert record[field] == value
    assert record["pmid"] == "12345678"


def test_nbib_load_write_as_bibtex(tmp_path: Path) -> None:
    records = load_records(DATA / "load_expected.bib")
    text = dumps(records, format="bib")
    output = tmp_path / "from-nbib.bib"
    write_records(records, path=output)

    assert "@article" in text
    assert load_records(output) == records
