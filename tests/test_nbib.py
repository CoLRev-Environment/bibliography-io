"""Tests for NBIB loading using the retained fixture."""

import json
from pathlib import Path

from bibliography_io import to_string
from bibliography_io import load_raw
from bibliography_io import loads_raw
from bibliography_io import write


DATA = Path(__file__).parent / "data" / "nbib"


def test_load_nbib_fixture() -> None:
    records = load_raw(DATA / "load.nbib")
    expected = json.loads((DATA / "load_expected.json").read_text(encoding="utf-8"))

    assert len(records) == len(expected) == 1
    assert records == expected


def test_load_nbib_non_normalized_retains_source_tags() -> None:
    records = load_raw(DATA / "load.nbib", normalize=False)

    assert records[0]["AU"] == ["Smith, Tom", "Hunter, Shawn"]
    assert records[0]["OT"] == ["Keyword 1", "Keyword 2", "Keyword 3"]
    assert records[0]["DP"] == "2000"
    assert records[0]["PMID"] == "12345678"


def test_nbib_repeated_publication_types_are_preserved() -> None:
    records = loads_raw(
        "PT  - Journal Articles\nPT  - Reports - Research\n",
        format="nbib",
        normalize=False,
    )

    assert records[0]["PT"] == ["Journal Articles", "Reports - Research"]


def test_nbib_single_publication_type_remains_a_scalar() -> None:
    records = loads_raw(
        "PT  - Journal Articles\n", format="nbib", normalize=False
    )

    assert records[0]["PT"] == "Journal Articles"


def test_nbib_repeated_normalized_publication_types_are_preserved() -> None:
    records = loads_raw(
        "PT  - Journal Articles\nPT  - Reports - Research\n", format="nbib"
    )

    assert records[0]["type"] == "journal_articles; reports_research"


def test_nbib_load_write_as_bibtex(tmp_path: Path) -> None:
    records = load_raw(DATA / "load.nbib")
    text = to_string(records, format="bib")
    output = tmp_path / "from-nbib.bib"
    write(records, path=output)

    assert "@article" in text
    written = load_raw(output)
    assert len(written) == len(records) == 1
    written_record = {key: value for key, value in written[0].items() if key != "ID"}
    assert written_record == records[0]
