"""Tests for the standalone public API (intentionally no CoLRev fixtures)."""

from pathlib import Path

import pytest

import bibliography_io as bibio
from bibliography_io.exceptions import DuplicateRecordIDError
from bibliography_io.exceptions import OptionalBackendUnavailableError
from bibliography_io.exceptions import ParseError
from bibliography_io.exceptions import UnsupportedFormatError
from bibliography_io.constants import ENTRYTYPES
from bibliography_io.constants import Fields
from bibliography_io.constants import Colors
from bibliography_io.writer.bib import to_string as bibtex_to_string


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
    other.write_text(
        '[{"ID":"sample","ENTRYTYPE":"article","title":"A | sample","year":"2024","custom":"retained"}]',
        encoding="utf-8",
    )
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
    records = bibio.loads(
        '[{"ID":"1","ENTRYTYPE":"article"},{"ENTRYTYPE":"article"}]', format="json"
    )
    assert list(records) == ["1", "2"]


def test_malformed_json_is_reported_as_parse_error() -> None:
    with pytest.raises(ParseError):
        bibio.loads("{", format="json")


def test_unknown_options_are_rejected() -> None:
    with pytest.raises(TypeError):
        bibio.load_records("items.bib", legacy_option=True)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        bibio.write_records(RECORDS, "items.bib", legacy_option=True)  # type: ignore[call-arg]


def test_package_owned_generic_constants() -> None:
    assert Fields.ID == "ID"
    assert Fields.TITLE == "title"
    assert ENTRYTYPES.ARTICLE == "article"
    assert ENTRYTYPES.get_all()
    assert Fields.STATUS == "colrev_status"
    assert not hasattr(bibio.constants, "RecordState")
    assert not hasattr(ENTRYTYPES, "SEARCH")
    assert Colors.ORANGE == "\033[93m"
    assert Colors.END == "\033[0m"


def test_bibtex_writer_preserves_legacy_colrev_metadata_formatting() -> None:
    record = {
        Fields.ID: "sample",
        Fields.ENTRYTYPE: "article",
        Fields.TITLE: "A sample",
        Fields.ORIGIN: ["z_source.bib/2", "a_source.bib/1"],
        Fields.MD_PROV: {"title": {"source": "provider", "note": "reviewed,verified"}},
    }
    text = bibtex_to_string(records_dict={"sample": record})
    assert text == (
        "@article{sample,\n"
        "   colrev_origin                 = {a_source.bib/1;\n"
        "                                    z_source.bib/2;},\n"
        "   colrev_masterdata_provenance  = {title:provider;reviewed,verified;},\n"
        "   title                         = {A sample},\n"
        "}\n"
    )


def test_bibtex_string_status_stays_raw_in_bibliography_io() -> None:
    records = bibio.loads("@article{sample, colrev_status={md_imported}}", format="bib")
    assert records["sample"]["colrev_status"] == "md_imported"
    assert isinstance(records["sample"]["colrev_status"], str)


def test_markdown_table_is_core_and_reference_parsing_is_optional(
    tmp_path: Path,
) -> None:
    assert "| title |" in bibio.dumps(RECORDS, format="md")
    path = tmp_path / "items.md"
    bibio.write_records(RECORDS, path)
    assert "| title |" in path.read_text(encoding="utf-8")
    with pytest.raises(OptionalBackendUnavailableError):
        bibio.loads("# References\n\nA reference", format="md")
