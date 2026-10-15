"""Tests for the standalone public API (intentionally no CoLRev fixtures)."""

from pathlib import Path

import pytest

import bibliography_io as bibio
from bibliography_io.exceptions import DuplicateRecordIDError
from bibliography_io.exceptions import OptionalBackendUnavailableError
from bibliography_io.exceptions import ParseError
from bibliography_io.exceptions import UnsupportedFormatError


RECORDS = {
    "sample": {
        "ID": "sample",
        "ENTRYTYPE": "article",
        "title": "A | sample",
        "year": "2024",
        "custom": "retained",
    }
}


@pytest.mark.parametrize("fmt", ["bib", "csv"])
def test_text_round_trip(fmt: str) -> None:
    text = bibio.dumps(RECORDS, format=fmt)
    records = bibio.loads(text, format=fmt)
    assert records["sample"]["ID"] == "sample"
    assert records["sample"]["custom"] == "retained"


def test_suffix_inference_and_explicit_format(tmp_path: Path) -> None:
    path = tmp_path / "items.bib"
    bibio.write_records(RECORDS, path)
    assert bibio.load_records(path) == RECORDS
    other = tmp_path / "items.data"
    other.write_text('[{"ID":"sample","ENTRYTYPE":"article","title":"A | sample","year":"2024","custom":"retained"}]', encoding="utf-8")
    assert bibio.load_records(other, format="json") == RECORDS


def test_missing_file_and_unknown_format(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        bibio.load_records(tmp_path / "missing.bib")
    with pytest.raises(UnsupportedFormatError):
        bibio.load_records(tmp_path / "items.unknown")


def test_duplicate_ids_are_rejected() -> None:
    with pytest.raises(DuplicateRecordIDError):
        bibio.dumps({"a": RECORDS["sample"], "b": RECORDS["sample"]}, format="bib")


def test_json_ids_are_generated_without_collisions() -> None:
    records = bibio.loads('[{"ID":"1","ENTRYTYPE":"article"},{"ENTRYTYPE":"article"}]', format="json")
    assert list(records) == ["1", "2"]


def test_malformed_json_is_reported_as_parse_error() -> None:
    with pytest.raises(ParseError):
        bibio.loads("{", format="json")


def test_unknown_options_are_rejected() -> None:
    with pytest.raises(TypeError):
        bibio.load_records("items.bib", legacy_option=True)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        bibio.write_records(RECORDS, "items.bib", legacy_option=True)  # type: ignore[call-arg]


def test_markdown_table_is_core_and_reference_parsing_is_optional(tmp_path: Path) -> None:
    assert "| title |" in bibio.dumps(RECORDS, format="md")
    path = tmp_path / "items.md"
    bibio.write_records(RECORDS, path)
    assert "| title |" in path.read_text(encoding="utf-8")
    with pytest.raises(OptionalBackendUnavailableError):
        bibio.loads("# References\n\nA reference", format="md")
