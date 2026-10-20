"""Tests for NBIB loading using the retained fixture."""

from pathlib import Path

from bibliography_io import dumps
from bibliography_io import load_records
from bibliography_io import write_records


DATA = Path(__file__).parent / "data" / "nbib"


def test_load_nbib_fixture() -> None:
    records = load_records(DATA / "load.nbib")
    expected = load_records(DATA / "load_expected.bib")
    record = next(iter(records.values()))
    expected_record = next(iter(expected.values()))
    assert record == expected_record
    assert record["ID"] == "1"
    assert record["pmid"] == "12345678"


def test_nbib_load_write_as_bibtex(tmp_path: Path) -> None:
    records = load_records(DATA / "load_expected.bib")
    text = dumps(records, format="bib")
    output = tmp_path / "from-nbib.bib"
    write_records(records, path=output)

    assert "@article" in text
    assert load_records(output) == records
