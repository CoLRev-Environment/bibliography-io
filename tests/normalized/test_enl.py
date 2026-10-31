"""Tests for normalized ENL loading."""

from pathlib import Path

from bibliography_io import load
from bibliography_io import load_raw

DATA = Path(__file__).parents[1] / "data" / "enl"


def test_load_enl_fixture() -> None:
    records = load(DATA / "load.enl")
    expected = load_raw(DATA / "load_expected.bib")

    assert len(records) == 3
    assert len(expected) == 1
    actual_first = next(
        record
        for record in records.values()
        if record["title"].startswith("How Trust Leads")
    )
    expected_first = next(
        record for record in expected if record["title"].startswith("How Trust Leads")
    )
    assert actual_first["ENTRYTYPE"] == "article"
    assert actual_first["author"] == expected_first["author"]
    assert actual_first["title"] == expected_first["title"]
    assert actual_first["ID"] == "1"

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
