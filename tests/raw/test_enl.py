"""Tests for ENL loading and writing using repository fixtures."""

from pathlib import Path

import pytest

from bibliography_io import load_raw, loads, loads_raw, to_string, write


DATA = Path(__file__).parents[1] / "data" / "enl"


def test_enl_load_raw_preserves_source_tags_and_repeated_values() -> None:
    records = load_raw(DATA / "load.enl")

    assert len(records) == 3
    assert records[0]["ENTRYTYPE"] == "article"
    assert records[0]["T"].startswith("How Trust Leads to Commitment")
    assert records[0]["A"] == [
        "Guo, Wenbo",
        "Straub, Detmar W.",
        "Zhang, Pengzhu",
        "Cai, Zhao",
    ]
    assert records[0]["D"] == "2021"


def test_enl_records_write_to_bibtex(tmp_path: Path) -> None:
    records = load_raw(DATA / "load_expected.bib")
    text = to_string(records, format="bib")
    output = tmp_path / "from-enl.bib"
    write(records, path=output)

    assert text.strip() == to_string(records, format="bib").strip()
    assert load_raw(output) == records


def test_enl_string_writer_round_trips_supported_fields() -> None:
    records = {
        "example": {
            "ID": "example",
            "ENTRYTYPE": "article",
            "title": "An example",
            "author": "One, A. and Two, B.",
            "year": "2024",
            "journal": "Example Journal",
            "volume": "12",
            "number": "3",
            "pages": "10-20",
            "date": "May 1, 2024",
            "url": "https://example.com",
            "abstract": "A summary",
            "doi": "10.1234/example",
            "keywords": "one; two",
            "editor": "Editor, E.",
            "publisher": "Example Press",
            "address": "Example City",
        }
    }

    text = to_string(records, format="enl")
    parsed = loads_raw(text, format="enl")
    normalized = loads(text, format="enl")

    assert text.startswith("%0 Journal Article\n%T An example\n%A One, A.\n%A Two, B.")
    assert parsed == [
        {
            "0": "Journal Article",
            "T": "An example",
            "A": ["One, A.", "Two, B."],
            "D": "2024",
            "B": "Example Journal",
            "V": "12",
            "N": "3",
            "P": "10-20",
            "8": "May 1, 2024",
            "U": "https://example.com",
            "X": "A summary",
            "R": "10.1234/example",
            "K": ["one", "two"],
            "E": "Editor, E.",
            "I": "Example Press",
            "C": "Example City",
            "ENTRYTYPE": "article",
        }
    ]
    assert normalized["1"] == {
        "ID": "1",
        "ENTRYTYPE": "article",
        "title": "An example",
        "author": "One, A. and Two, B.",
        "year": "2024",
        "journal": "Example Journal",
        "volume": "12",
        "number": "3",
        "pages": "10-20",
        "date": "May 1, 2024",
        "url": "https://example.com",
        "abstract": "A summary",
        "doi": "10.1234/example",
        "keywords": "one; two",
        "editor": "Editor, E.",
        "publisher": "Example Press",
        "address": "Example City",
    }


def test_enl_writer_warns_and_skips_unknown_fields() -> None:
    records = {"example": {"ENTRYTYPE": "article", "custom_field": "ignored"}}

    with pytest.warns(
        UserWarning, match="Skipping unsupported ENL field 'custom_field'"
    ):
        text = to_string(records, format="enl")

    assert text == "%0 Journal Article"


def test_enl_file_writer(tmp_path: Path) -> None:
    records = [{"ID": "example", "ENTRYTYPE": "article", "title": "An example"}]
    output = tmp_path / "output.enl"

    write(records, path=output)

    assert output.read_text(encoding="utf-8") == "%0 Journal Article\n%T An example"
