"""Tests for ENL loading and serialization using repository fixtures."""

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
        record
        for record in records.values()
        if record["title"].startswith("How Trust Leads")
    )
    expected_first = next(
        record
        for record in expected.values()
        if record["title"].startswith("How Trust Leads")
    )
    expected_for_enl = dict(expected_first)
    expected_for_enl["type"] = "journal_article"
    assert actual_first == expected_for_enl

    assert records["2"]["title"].startswith("Microsourcing - Using Information")
    assert records["2"]["author"] == "Obal, Lorie"
    assert records["2"]["year"] == "2009"
    assert records["2"]["volume"] == "24"
    assert records["2"]["number"] == "1"
    assert records["2"]["abstract"].startswith("Offshore outsourcing has increased")

    assert records["3"]["title"] == "MISQ Volume 45, Issue 3 Table of Contents"
    assert records["3"]["year"] == "2021"
    assert records["3"]["volume"] == "45"
    assert records["3"]["number"] == "3"
    assert records["3"]["pages"] == "i-ii"


def test_enl_records_write_to_bibtex(tmp_path: Path) -> None:
    records = load_records(DATA / "load_expected.bib")
    text = dumps(records, format="bib")
    output = tmp_path / "from-enl.bib"
    write_records(records, path=output)

    assert text.strip() == dumps(records, format="bib").strip()
    assert load_records(output) == records
