"""Tests for BibTeX file APIs using format-specific fixtures."""

from pathlib import Path

import pytest

from bibliography_io import dumps
from bibliography_io import load_records
from bibliography_io import loads
from bibliography_io import write_records
from bibliography_io.exceptions import ParseError
from bibliography_io.exceptions import RecordValidationError
from bibliography_io.exceptions import SerializationError
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
    write_records(records, path=output)

    assert text.strip() == expected_text.strip()
    assert load_records(output) == records


def test_malformed_bibtex_raises_parse_error() -> None:
    with pytest.raises(ParseError):
        loads("not a BibTeX entry", format="bib")


def test_unknown_suffix_raises_unsupported_format(tmp_path: Path) -> None:
    with pytest.raises(UnsupportedFormatError):
        load_records(tmp_path / "records.unknown")


def test_declared_nested_mapping_round_trip() -> None:
    provenance = {"CURATED": {"source": "github...", "note": ""}}
    records = {
        "example": {"ENTRYTYPE": "article", "colrev_masterdata_provenance": provenance}
    }

    encoded = dumps(
        records,
        format="bib",
        mapping_fields=["colrev_masterdata_provenance"],
    )
    parsed = loads(
        encoded,
        format="bib",
        mapping_fields=["colrev_masterdata_provenance"],
    )

    assert parsed["example"]["colrev_masterdata_provenance"] == provenance
    assert "bibio-json-v1:" in encoded


def test_declared_nested_lists_round_trip() -> None:
    value = ["a", [1, True, None], {"nested": ["text", {"empty": []}]}]
    records = {"example": {"ENTRYTYPE": "misc", "custom_list": value}}
    encoded = dumps(records, format="bib", list_fields=["custom_list"])

    assert (
        loads(encoded, format="bib", list_fields=["custom_list"])["example"][
            "custom_list"
        ]
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
    encoded = dumps(records, format="bib", **declaration)

    assert loads(encoded, format="bib", **declaration)["example"][field] == value


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
    text = dumps(records, format="bib", mapping_fields=["data"])

    assert (
        loads(text, format="bib", mapping_fields=["data"])["example"]["data"] == value
    )


def test_undeclared_structures_keep_serialization_error() -> None:
    records = {
        "example": {
            "ENTRYTYPE": "misc",
            "mapping": {"nested": []},
            "items": [1, {"nested": "value"}],
        }
    }

    with pytest.raises(SerializationError, match="non-scalar"):
        dumps(records, format="bib")


def test_malformed_declared_structured_value_raises_chained_parse_error() -> None:
    malformed_values = [
        "bibio-json-v1:not-base64!",
        "bibio-json-v1:bm90LWpzb24=",  # valid Base64, invalid JSON
    ]
    for value in malformed_values:
        text = f"@misc{{example, data={{{value}}}}}"
        with pytest.raises(ParseError, match="Malformed structured value") as error:
            loads(text, format="bib", mapping_fields=["data"])
        assert error.value.__cause__ is not None


def test_declared_field_rejects_wrong_top_level_structured_type() -> None:
    records = {"example": {"ENTRYTYPE": "misc", "data": ["item"]}}
    text = dumps(records, format="bib", list_fields=["data"])

    with pytest.raises(ParseError, match="declared as a mapping field"):
        loads(text, format="bib", mapping_fields=["data"])


def test_structured_option_rejected_for_irrelevant_formats() -> None:
    with pytest.raises(UnsupportedFormatError, match="only supported for BibTeX"):
        dumps({"example": {"ENTRYTYPE": "misc"}}, format="json", list_fields=["data"])


def test_structured_field_declaration_must_be_unambiguous() -> None:
    with pytest.raises(RecordValidationError, match="both mappings and lists"):
        dumps(
            {"example": {"ENTRYTYPE": "misc"}},
            format="bib",
            mapping_fields=["data"],
            list_fields=["data"],
        )


def test_structured_file_api_round_trip(tmp_path: Path) -> None:
    value = {"CURATED": {"source": "github...", "note": ""}}
    records = {"example": {"ENTRYTYPE": "article", "provenance": value}}
    path = tmp_path / "structured.bib"

    write_records(records, path=path, mapping_fields=["provenance"])

    assert (
        load_records(path, mapping_fields=["provenance"])["example"]["provenance"]
        == value
    )
