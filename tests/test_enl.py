"""Tests for ENL loading and writing using repository fixtures."""

from pathlib import Path

from bibliography_io import dumps
from bibliography_io import load_records
from bibliography_io import write_records


DATA = Path(__file__).parent / "data" / "enl"


def test_load_enl_fixture() -> None:
    records = load_records(DATA / "load.enl")
    expected = load_records(DATA / "load_expected.bib")

    assert len(records) == 3
    assert len(expected) == 1
    actual_first = next(
        record for record in records if record["title"].startswith("How Trust Leads")
    )
    expected_first = next(
        record for record in expected if record["title"].startswith("How Trust Leads")
    )
    expected_for_enl = dict(expected_first)
    expected_for_enl["type"] = "journal_article"
    assert {key: value for key, value in actual_first.items() if key != "ID"} == {
        key: value for key, value in expected_for_enl.items() if key != "ID"
    }

    assert records[1]["title"].startswith("Microsourcing - Using Information")
    assert records[1]["author"] == "Obal, Lorie"
    assert records[1]["year"] == "2009"
    assert records[1]["volume"] == "24"
    assert records[1]["number"] == "1"
    assert records[1]["abstract"].startswith("Offshore outsourcing has increased")

    assert records[2]["title"] == "MISQ Volume 45, Issue 3 Table of Contents"
    assert records[2]["year"] == "2021"
    assert records[2]["volume"] == "45"
    assert records[2]["number"] == "3"
    assert records[2]["pages"] == "i-ii"


def test_enl_records_write_to_bibtex(tmp_path: Path) -> None:
    records = load_records(DATA / "load_expected.bib")
    text = dumps(records, format="bib")
    output = tmp_path / "from-enl.bib"
    write_records(records, path=output)

    assert text.strip() == dumps(records, format="bib").strip()
    assert load_records(output) == records
