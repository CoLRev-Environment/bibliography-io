"""Tests for NBIB loading using the retained fixture."""

from pathlib import Path

from bibliography_io import load_raw, loads_raw


DATA = Path(__file__).parents[1] / "data" / "nbib"


def test_load_nbib_non_normalized_retains_source_tags() -> None:
    records = load_raw(DATA / "load.nbib")

    assert records[0]["ENTRYTYPE"] == "article"
    assert records[0]["TI"] == "Paper title"
    assert records[0]["AU"] == ["Smith, Tom", "Hunter, Shawn"]
    assert records[0]["OT"] == ["Keyword 1", "Keyword 2", "Keyword 3"]
    assert records[0]["DP"] == "2000"
    assert records[0]["PMID"] == "12345678"


def test_nbib_repeated_publication_types_are_preserved() -> None:
    records = loads_raw(
        "PT  - Journal Articles\nPT  - Reports - Research\n",
        format="nbib",
    )

    assert records[0]["PT"] == ["Journal Articles", "Reports - Research"]


def test_nbib_repeated_authors_are_preserved_as_a_list() -> None:
    records = loads_raw("AU  - Smith, Tom\nAU  - Hunter, Shawn\n", format="nbib")

    assert records[0]["AU"] == ["Smith, Tom", "Hunter, Shawn"]


def test_nbib_single_publication_type_remains_a_scalar() -> None:
    records = loads_raw("PT  - Journal Articles\n", format="nbib")

    assert records[0]["PT"] == "Journal Articles"


def test_nbib_repeated_publication_types_remain_parser_level_values() -> None:
    records = loads_raw(
        "PT  - Journal Articles\nPT  - Reports - Research\n", format="nbib"
    )

    assert records[0]["PT"] == ["Journal Articles", "Reports - Research"]
