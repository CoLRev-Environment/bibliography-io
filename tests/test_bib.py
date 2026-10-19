"""Tests for BibTeX file APIs using format-specific fixtures."""

from pathlib import Path

import pytest

from bibliography_io import dumps
from bibliography_io import load_records
from bibliography_io import loads
from bibliography_io import write_records
from bibliography_io.exceptions import ParseError
from bibliography_io.exceptions import UnsupportedFormatError


DATA = Path(__file__).parent / "data" / "bib"
ORIGINAL_DUPLICATE_FIXTURE = DATA / "load.bib"


def test_loading_preserves_duplicate_record_ids() -> None:
    records = load_records(ORIGINAL_DUPLICATE_FIXTURE)
    repeated = [
        record
        for record in records.values()
        if record["ID"] == "articlewriter_firstrandomword_2020"
    ]

    assert len(repeated) == 2
    assert len(set(records)) == len(records)
    assert {record["doi"] for record in repeated} == {"10.3333/XYZ.V4444.04a"}


def test_loading_matches_expected_bibtex() -> None:
    records = load_records(DATA / "load.bib")
    expected = load_records(DATA / "load_expected.bib")

    assert len(records) == len(expected)
    assert list(records) == list(expected)
    for record, expected_record in zip(records.values(), expected.values()):
        assert record["ENTRYTYPE"] == expected_record["ENTRYTYPE"]
        assert record["ID"] == expected_record["ID"]
        for key, expected_value in expected_record.items():
            actual_value = record[key]
            if isinstance(actual_value, str) and isinstance(expected_value, str):
                assert " ".join(actual_value.split()) == " ".join(
                    expected_value.split()
                )
            else:
                assert actual_value == expected_value
        assert set(record) >= set(expected_record)


def test_unique_id_round_trip_uses_expected_fixtures(tmp_path: Path) -> None:
    records = load_records(DATA / "write_expected.bib")
    expected_text = (DATA / "write_expected.bib").read_text(encoding="utf-8")
    text = dumps(records, format="bib")
    output = tmp_path / "written.bib"
    write_records(records, output)

    assert text.strip() == expected_text.strip()
    assert load_records(output) == records


def test_malformed_bibtex_raises_parse_error() -> None:
    with pytest.raises(ParseError):
        loads("not a BibTeX entry", format="bib")


def test_unknown_suffix_raises_unsupported_format(tmp_path: Path) -> None:
    with pytest.raises(UnsupportedFormatError):
        load_records(tmp_path / "records.unknown")
