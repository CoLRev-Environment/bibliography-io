"""Tests for ENL loading and serialization using repository fixtures."""

from pathlib import Path

from bibliography_io import dumps
from bibliography_io import load_records
from bibliography_io import loads
from bibliography_io import write_records


DATA = Path(__file__).parent / "data" / "enl"


def test_load_enl_fixture() -> None:
    records = load_records(DATA / "load.enl")
    expected = load_records(DATA / "load_expected.bib")

    assert len(records) == 3
    assert len(expected) == 1
    actual_first = next(
        record
        for record in records.values()
        if record["title"].startswith("How Trust Leads")
    )
    expected_first = next(
        record
        for record in expected.values()
        if record["title"].startswith("How Trust Leads")
    )
    for field in ("title", "author", "journal", "year"):
        assert actual_first[field] == expected_first[field]


def test_enl_records_write_to_bibtex(tmp_path: Path) -> None:
    records = loads("%T A sample\n%A Doe, Jane\n%D 2024\n\n", format="enl")
    text = dumps(records, format="bib")
    output = tmp_path / "from-enl.bib"
    write_records(records, output)

    assert "@article" in text
    assert load_records(output) == records
