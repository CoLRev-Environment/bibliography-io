"""Tests for BibTeX file APIs using format-specific fixtures."""

from pathlib import Path

import pytest

from bibliography_io import to_string
from bibliography_io import load_raw
from bibliography_io import loads_raw
from bibliography_io import write
from bibliography_io.exceptions import ParseError
from bibliography_io.exceptions import RecordValidationError
from bibliography_io.exceptions import SerializationError
from bibliography_io.exceptions import UnsupportedFormatError


DATA = Path(__file__).parent / "data" / "bib"
ORIGINAL_DUPLICATE_FIXTURE = DATA / "load.bib"


def test_loading_preserves_duplicate_record_ids() -> None:
    records = load_raw(ORIGINAL_DUPLICATE_FIXTURE)
    repeated = [
        record
        for record in records
        if record["ID"] == "articlewriter_firstrandomword_2020"
    ]

    assert len(repeated) == 2
    assert len(records) == 6
    assert {record["doi"] for record in repeated} == {
        "10.3333/XYZ.V4444.04",
        "10.3333/XYZ.V4444.04a",
    }


def test_loading_matches_expected_bibtex() -> None:
    records = load_raw(DATA / "load.bib")
    expected = load_raw(DATA / "load_expected.bib")

    assert len(records) == len(expected)
    for record, expected_record in zip(records, expected):
        assert record["ENTRYTYPE"] == expected_record["ENTRYTYPE"]
        assert record["ID"].split("#", 1)[0] == expected_record["ID"].split("#", 1)[0]
        for key, expected_value in expected_record.items():
            if key == "ID":
                continue
            actual_value = record[key]
            if isinstance(actual_value, str) and isinstance(expected_value, str):
                assert " ".join(actual_value.split()) == " ".join(
                    expected_value.split()
                )
            else:
                assert actual_value == expected_value
        assert set(record) >= set(expected_record)


def test_unique_id_round_trip_uses_expected_fixtures(tmp_path: Path) -> None:
    records = load_raw(DATA / "write_expected.bib")
    expected_text = (DATA / "write_expected.bib").read_text(encoding="utf-8")
    text = to_string(records, format="bib")
    output = tmp_path / "written.bib"
    write(records, path=output)

    assert text.strip() == expected_text.strip()
    assert load_raw(output) == records


def test_bibtex_writer_aligns_fields_per_entry() -> None:
    records = {
        "first": {
            "ENTRYTYPE": "article",
            "author": "Example, Alex",
            "colrev_status": "md_prepared",
            "ID": "first",
        },
        "second": {
            "ENTRYTYPE": "misc",
            "title": "Standalone",
            "ID": "second",
        },
    }

    text = to_string(records, format="bib")

    assert text == (
        "@article{first,\n"
        "  author        = {Example, Alex},\n"
        "  colrev_status = {md_prepared}\n"
        "}\n\n"
        "@misc{second,\n"
        "  title = {Standalone}\n"
        "}"
    )


def test_malformed_bibtex_raises_parse_error() -> None:
    with pytest.raises(ParseError):
        loads_raw("not a BibTeX entry", format="bib")


def test_unknown_suffix_raises_unsupported_format(tmp_path: Path) -> None:
    with pytest.raises(UnsupportedFormatError):
        load_raw(tmp_path / "records.unknown")


def test_declared_nested_mapping_round_trip() -> None:
    provenance = {"CURATED": {"source": "github...", "note": ""}}
    records = {
        "example": {"ENTRYTYPE": "article", "colrev_masterdata_provenance": provenance}
    }

    encoded = to_string(
        records,
        format="bib",
        mapping_fields=["colrev_masterdata_provenance"],
    )
    parsed = loads_raw(
        encoded,
        format="bib",
        mapping_fields=["colrev_masterdata_provenance"],
    )

    assert parsed[0]["colrev_masterdata_provenance"] == provenance
    assert "bibio-json-v1:" in encoded


def test_declared_nested_lists_round_trip() -> None:
    value = ["a", [1, True, None], {"nested": ["text", {"empty": []}]}]
    records = {"example": {"ENTRYTYPE": "misc", "custom_list": value}}
    encoded = to_string(records, format="bib", list_fields=["custom_list"])

    assert (
        loads_raw(encoded, format="bib", list_fields=["custom_list"])[0]["custom_list"]
        == value
    )


@pytest.mark.parametrize("value", [{}, [], {"empty": []}, [{}, []]])
def test_empty_and_nested_empty_structures_round_trip(value: object) -> None:
    field = "data"
    declaration = (
        {"mapping_fields": [field]}
        if isinstance(value, dict)
        else {"list_fields": [field]}
    )
    records = {"example": {"ENTRYTYPE": "misc", field: value}}
    encoded = to_string(records, format="bib", **declaration)

    assert loads_raw(encoded, format="bib", **declaration)[0][field] == value


def test_structured_values_escape_arbitrary_text_and_preserve_scalar_types() -> None:
    value = {
        'key;=,{}"': [
            'brace { nested } and "quote"',
            r"backslash \\ and slash /",
            "Unicode: café 雪 🧪",
            False,
            1,
            1.25,
            None,
        ]
    }
    records = {"example": {"ENTRYTYPE": "misc", "data": value}}
    text = to_string(records, format="bib", mapping_fields=["data"])

    assert loads_raw(text, format="bib", mapping_fields=["data"])[0]["data"] == value


def test_undeclared_structures_keep_writing_error() -> None:
    records = {
        "example": {
            "ENTRYTYPE": "misc",
            "mapping": {"nested": []},
            "items": [1, {"nested": "value"}],
        }
    }

    with pytest.raises(SerializationError, match="non-scalar"):
        to_string(records, format="bib")


def test_malformed_declared_structured_value_raises_chained_parse_error() -> None:
    malformed_values = [
        "bibio-json-v1:not-base64!",
        "bibio-json-v1:bm90LWpzb24=",  # valid Base64, invalid JSON
    ]
    for value in malformed_values:
        text = f"@misc{{example, data={{{value}}}}}"
        with pytest.raises(ParseError, match="Malformed structured value") as error:
            loads_raw(text, format="bib", mapping_fields=["data"])
        assert error.value.__cause__ is not None


def test_declared_field_rejects_wrong_top_level_structured_type() -> None:
    records = {"example": {"ENTRYTYPE": "misc", "data": ["item"]}}
    text = to_string(records, format="bib", list_fields=["data"])

    with pytest.raises(ParseError, match="declared as a mapping field"):
        loads_raw(text, format="bib", mapping_fields=["data"])


def test_structured_option_rejected_for_irrelevant_formats() -> None:
    with pytest.raises(UnsupportedFormatError, match="only supported for BibTeX"):
        to_string(
            {"example": {"ENTRYTYPE": "misc"}}, format="json", list_fields=["data"]
        )


def test_structured_field_declaration_must_be_unambiguous() -> None:
    with pytest.raises(RecordValidationError, match="both mappings and lists"):
        to_string(
            {"example": {"ENTRYTYPE": "misc"}},
            format="bib",
            mapping_fields=["data"],
            list_fields=["data"],
        )


def test_structured_file_api_round_trip(tmp_path: Path) -> None:
    value = {"CURATED": {"source": "github...", "note": ""}}
    records = {"example": {"ENTRYTYPE": "article", "provenance": value}}
    path = tmp_path / "structured.bib"

    write(records, path=path, mapping_fields=["provenance"])

    assert load_raw(path, mapping_fields=["provenance"])[0]["provenance"] == value


def test_raw_bibtex_preserves_missing_duplicate_and_hash_ids() -> None:
    records = loads_raw(
        "@article{same#key, title={First}}\n@article{same#key, title={Second}}",
        format="bib",
    )
    assert [record.get("ID") for record in records] == ["same#key", "same#key"]
    assert [record["title"] for record in records] == ["First", "Second"]
    assert loads_raw('[{"title": "No ID"}]', format="json")[0].get("ID") is None
