"""Tests for BibTeX file APIs using format-specific fixtures."""

from pathlib import Path

import pytest

from bibliography_io import load_raw
from bibliography_io import loads_raw
from bibliography_io import to_string
from bibliography_io import update
from bibliography_io import write
from bibliography_io import write_string
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


def test_update_replaces_matching_records_and_preserves_other_bytes(
    tmp_path: Path,
) -> None:
    path = tmp_path / "records.bib"
    untouched = b"@misc{keep,\n   title = {Keep exactly},\n}\n\n"
    path.write_bytes(
        b"% bibliography header\n"
        b"@article{replace,\n   title = {Old},\n}\n\n" + untouched
    )

    update(
        path,
        {
            "replace": {
                "ID": "replace",
                "ENTRYTYPE": "article",
                "title": "A much longer replacement",
            }
        },
    )

    content = path.read_bytes()
    assert content.startswith(b"% bibliography header\n")
    assert b"title                         = {A much longer replacement}" in content
    assert content.endswith(untouched)


def test_update_appends_records_missing_from_file(tmp_path: Path) -> None:
    path = tmp_path / "records.bib"
    path.write_text("@misc{existing,\n}\n", encoding="utf-8")

    update(
        path,
        {"new": {"ID": "new", "ENTRYTYPE": "article", "title": "New"}},
    )

    content = path.read_text(encoding="utf-8")
    assert "@misc{existing," in content
    assert "@article{new," in content


def test_update_handles_shorter_replacement(tmp_path: Path) -> None:
    path = tmp_path / "records.bib"
    path.write_text(
        "@article{replace,\n   title = {A very long old value},\n}\n\n"
        "@misc{keep,\n   title = {Keep},\n}",
        encoding="utf-8",
    )

    update(
        path,
        {"replace": {"ID": "replace", "ENTRYTYPE": "article", "title": "Short"}},
    )

    content = path.read_text(encoding="utf-8")
    assert "title                         = {Short}" in content
    assert content.endswith("@misc{keep,\n   title = {Keep},\n}")


def test_update_creates_file_and_serializes_structured_fields(tmp_path: Path) -> None:
    path = tmp_path / "new.bib"
    update(
        path,
        {
            "new": {
                "ID": "new",
                "ENTRYTYPE": "article",
                "colrev_origin": ["source"],
                "colrev_masterdata_provenance": {
                    "title": {"source": "source", "note": ""}
                },
            }
        },
        mapping_fields={"colrev_masterdata_provenance"},
        list_fields={"colrev_origin"},
    )

    record = load_raw(
        path,
        mapping_fields={"colrev_masterdata_provenance"},
        list_fields={"colrev_origin"},
    )[0]
    assert record["colrev_origin"] == ["source"]
    assert record["colrev_masterdata_provenance"]["title"]["source"] == "source"


def test_update_requires_mapping_keys_to_match_record_ids(tmp_path: Path) -> None:
    with pytest.raises(RecordValidationError, match="does not match its ID"):
        update(
            tmp_path / "records.bib",
            {"mapping-key": {"ID": "record-id", "ENTRYTYPE": "article"}},
        )


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
        "   colrev_status                 = {md_prepared},\n"
        "   author                        = {Example, Alex},\n"
        "}\n\n"
        "@misc{second,\n"
        "   title                         = {Standalone},\n"
        "}"
    )


def test_bibtex_writer_uses_fixed_field_width_for_long_field_names() -> None:
    records = {
        "example": {
            "ENTRYTYPE": "misc",
            "title": "Title",
            "colrev.vendor.identifier_that_exceeds_padding": "value",
        }
    }

    text = to_string(records, format="bib")

    assert "   title                         = {Title}," in text
    assert "   colrev.vendor.identifier_that_exceeds_padding  = {value}," in text


def test_bibtex_writer_preserves_dashes_in_colrev_extension_fields() -> None:
    records = {
        "example": {
            "ENTRYTYPE": "article",
            "ID": "example",
            "colrev.web_of_science.unique-id": "WOS:123",
            "colrev.web_of_science.article-number": "6756",
            "article-number": "ordinary field",
        }
    }

    text = to_string(records, format="bib")

    assert "colrev.web_of_science.unique-id" in text
    assert "colrev.web_of_science.article-number" in text
    assert "article_number" in text
    assert loads_raw(text, format="bib")[0]["colrev.web_of_science.unique-id"] == (
        "WOS:123"
    )


@pytest.mark.parametrize(
    "value",
    [
        "The Journal for {CAPITALLETTER} easy writing",
        "The Journal for {CAPITAL {NESTED} GROUP} easy writing",
    ],
)
def test_bibtex_writer_preserves_nested_braces(value: str) -> None:
    records = {"example": {"ENTRYTYPE": "article", "journal": value}}

    text = to_string(records, format="bib")

    assert f"{{{value}}}" in text
    assert r"\}" not in text
    assert loads_raw(text, format="bib")[0]["journal"] == value


@pytest.mark.parametrize("value", ["unmatched }", "unmatched {"])
def test_bibtex_writer_rejects_unbalanced_braces(value: str) -> None:
    records = {"example": {"ENTRYTYPE": "article", "title": value}}

    with pytest.raises(SerializationError, match="unbalanced braces"):
        to_string(records, format="bib")


def test_bibtex_writer_uses_default_colrev_field_order() -> None:
    fields = [
        "colrev_origin",
        "colrev_status",
        "colrev_masterdata_provenance",
        "colrev_data_provenance",
        "colrev_pdf_id",
        "screening_criteria",
        "file",
        "prescreen_exclusion",
        "doi",
        "grobid-version",
        "colrev.dblp.dblp_key",
        "colrev.semantic_scholar.id",
        "colrev.web_of_science.unique-id",
        "author",
        "booktitle",
        "journal",
        "title",
        "year",
        "volume",
        "number",
        "pages",
        "editor",
        "publisher",
        "url",
        "abstract",
    ]
    records = {
        "example": {
            "ENTRYTYPE": "article",
            "ID": "example",
            **{field: field for field in reversed(fields)},
        }
    }

    text = to_string(records, format="bib")

    expected_order = [
        "colrev_origin",
        "colrev_status",
        "colrev_masterdata_provenance",
        "colrev_data_provenance",
        "colrev_pdf_id",
        "screening_criteria",
        "file",
        "prescreen_exclusion",
        "doi",
        "grobid_version",
        "colrev.dblp.dblp_key",
        "colrev.semantic_scholar.id",
        "colrev.web_of_science.unique-id",
        "author",
        "booktitle",
        "journal",
        "title",
        "year",
        "volume",
        "number",
        "pages",
        "editor",
        "publisher",
        "url",
        "abstract",
    ]
    actual_order = [
        line.split(" = ", 1)[0].strip() for line in text.splitlines() if " = " in line
    ]
    assert actual_order == expected_order


def test_bibtex_writer_sorts_unlisted_fields_alphabetically() -> None:
    records = {
        "example": {
            "ENTRYTYPE": "article",
            "custom_second": "second",
            "title": "Title",
            "doi": "10.1234/example",
            "custom_first": "first",
            "ID": "example",
        }
    }

    text = to_string(records, format="bib", field_order=["doi", "title"])

    actual_order = [
        line.split(" = ", 1)[0].strip() for line in text.splitlines() if " = " in line
    ]
    assert actual_order == ["doi", "title", "custom_first", "custom_second"]


def test_bibtex_default_order_sorts_extra_fields_after_colrev_fields() -> None:
    records = {
        "example": {
            "ENTRYTYPE": "article",
            "custom_z": "last alphabetically",
            "title": "Title",
            "custom_a": "first alphabetically",
            "author": "Author",
        }
    }

    text = to_string(records, format="bib")

    actual_order = [
        line.split(" = ", 1)[0].strip() for line in text.splitlines() if " = " in line
    ]
    assert actual_order == ["author", "title", "custom_a", "custom_z"]


def test_bibtex_writer_can_preserve_all_field_input_order() -> None:
    records = {
        "example": {
            "ENTRYTYPE": "article",
            "custom_z": "last alphabetically",
            "title": "Title",
            "custom_a": "first alphabetically",
            "doi": "10.1234/example",
            "ID": "example",
        }
    }

    text = to_string(records, format="bib", sort_fields=False)
    dispatched_text = write_string(records, "bib", sort_fields=False)

    actual_order = [
        line.split(" = ", 1)[0].strip() for line in text.splitlines() if " = " in line
    ]
    assert actual_order == ["custom_z", "title", "custom_a", "doi"]
    assert dispatched_text == text


def test_bibtex_writer_custom_order_and_sort_opt_out() -> None:
    records = {
        "example": {
            "ENTRYTYPE": "article",
            "custom_z": "last alphabetically",
            "title": "Title",
            "custom_a": "first alphabetically",
            "doi": "10.1234/example",
            "ID": "example",
        }
    }

    sorted_text = to_string(records, format="bib", field_order=["doi", "title"])
    preserved_text = to_string(
        records, format="bib", field_order=["doi", "title"], sort_fields=False
    )

    def field_names(text: str) -> list[str]:
        return [
            line.split(" = ", 1)[0].strip()
            for line in text.splitlines()
            if " = " in line
        ]

    assert field_names(sorted_text) == ["doi", "title", "custom_a", "custom_z"]
    assert field_names(preserved_text) == ["custom_z", "title", "custom_a", "doi"]


def test_sort_fields_does_not_change_non_bibtex_output() -> None:
    records = {
        "example": {
            "ENTRYTYPE": "article",
            "title": "Title",
            "author": "Author",
            "ID": "example",
        }
    }

    assert to_string(records, format="ris", sort_fields=True) == to_string(
        records, format="ris", sort_fields=False
    )


def test_sort_fields_must_be_a_boolean() -> None:
    with pytest.raises(TypeError, match="sort_fields must be a bool"):
        to_string({"example": {"ENTRYTYPE": "article"}}, format="bib", sort_fields=1)


def test_file_writer_accepts_custom_field_order(tmp_path: Path) -> None:
    output = tmp_path / "ordered.bib"
    write(
        {
            "example": {
                "ENTRYTYPE": "article",
                "title": "Title",
                "author": "Author",
            }
        },
        path=output,
        field_order=["title", "author"],
    )

    text = output.read_text(encoding="utf-8")
    actual_order = [
        line.split(" = ", 1)[0].strip() for line in text.splitlines() if " = " in line
    ]
    assert actual_order == ["title", "author"]


def test_file_writer_can_preserve_field_input_order(tmp_path: Path) -> None:
    output = tmp_path / "input-order.bib"
    write(
        {
            "example": {
                "ENTRYTYPE": "article",
                "custom_z": "last alphabetically",
                "title": "Title",
                "custom_a": "first alphabetically",
            }
        },
        path=output,
        sort_fields=False,
    )

    actual_order = [
        line.split(" = ", 1)[0].strip()
        for line in output.read_text(encoding="utf-8").splitlines()
        if " = " in line
    ]
    assert actual_order == ["custom_z", "title", "custom_a"]


def test_field_order_is_bibtex_only_and_validated() -> None:
    records = {"example": {"ENTRYTYPE": "article"}}

    with pytest.raises(UnsupportedFormatError, match="only supported for BibTeX"):
        to_string(records, format="json", field_order=["title"])
    with pytest.raises(RecordValidationError, match="iterable of field names"):
        to_string(records, format="bib", field_order="title")
    with pytest.raises(RecordValidationError, match="duplicate fields"):
        to_string(records, format="bib", field_order=["title", "TITLE"])


def test_malformed_bibtex_raises_parse_error() -> None:
    with pytest.raises(ParseError):
        loads_raw("not a BibTeX entry", format="bib")


def test_bibtex_dotted_field_names_are_preserved_when_loading() -> None:
    text = "@article{example, colrev.vendor.identifier={abc123}}"

    normalized = loads_raw(text, format="bib")
    un_normalized = loads_raw(text, format="bib", normalize=False)

    assert normalized[0]["colrev.vendor.identifier"] == "abc123"
    assert un_normalized[0]["colrev.vendor.identifier"] == "abc123"
    assert "colrev_vendor_identifier" not in normalized[0]


def test_bibtex_dotted_field_names_are_preserved_when_writing(tmp_path: Path) -> None:
    records = {
        "example": {
            "ID": "example",
            "ENTRYTYPE": "article",
            "colrev.vendor.identifier": "abc123",
        }
    }

    text = to_string(records, format="bib", field_order=["colrev.vendor.identifier"])
    output = tmp_path / "dotted.bib"
    write(records, path=output, field_order=["colrev.vendor.identifier"])

    assert "colrev.vendor.identifier" in text
    assert load_raw(output)[0]["colrev.vendor.identifier"] == "abc123"


def test_unknown_suffix_raises_unsupported_format(tmp_path: Path) -> None:
    with pytest.raises(UnsupportedFormatError):
        load_raw(tmp_path / "records.unknown")


def test_declared_provenance_mapping_uses_legacy_format_and_round_trips() -> None:
    provenance = {
        "author": {"source": "ebsco_bib.bib/11111111111111111", "note": ""},
        "title": {"source": "manual.bib/entry1", "note": "checked"},
    }
    records = {
        "example": {"ENTRYTYPE": "article", "colrev_masterdata_provenance": provenance}
    }

    text = to_string(
        records,
        format="bib",
        mapping_fields=["colrev_masterdata_provenance"],
    )
    parsed = loads_raw(
        text,
        format="bib",
        mapping_fields=["colrev_masterdata_provenance"],
    )

    assert parsed[0]["colrev_masterdata_provenance"] == provenance
    assert (
        "   colrev_masterdata_provenance  = {author:ebsco_bib.bib/11111111111111111;;\n"
        "                                    title:manual.bib/entry1;checked;}," in text
    )


def test_declared_lists_use_semicolon_format_and_round_trip() -> None:
    value = ["CROSSREF.bib/001792", "DBLP.bib/001703"]
    records = {"example": {"ENTRYTYPE": "misc", "custom_list": value}}
    text = to_string(records, format="bib", list_fields=["custom_list"])

    assert (
        loads_raw(text, format="bib", list_fields=["custom_list"])[0]["custom_list"]
        == value
    )
    assert (
        f"   {'custom_list':<28}  = {{CROSSREF.bib/001792;\n"
        "                                    DBLP.bib/001703;}," in text
    )


def test_empty_declared_mapping_and_list_are_omitted() -> None:
    records = {"example": {"ENTRYTYPE": "misc", "provenance": {}, "origins": []}}
    text = to_string(
        records,
        format="bib",
        mapping_fields=["provenance"],
        list_fields=["origins"],
    )

    parsed = loads_raw(
        text,
        format="bib",
        mapping_fields=["provenance"],
        list_fields=["origins"],
    )
    assert "provenance" not in parsed[0]
    assert "origins" not in parsed[0]


def test_bibtex_writer_skips_only_exact_empty_string_dict_and_list() -> None:
    records = {
        "example": {
            "ENTRYTYPE": "misc",
            "empty_string": "",
            "empty_mapping": {},
            "empty_list": [],
            "none_value": None,
            "whitespace": " ",
            "nan_value": float("nan"),
        }
    }

    text = to_string(records, format="bib")

    assert "empty_string" not in text
    assert "empty_mapping" not in text
    assert "empty_list" not in text
    assert "none_value" in text and "{None}" in text
    assert "whitespace" in text and "{ }" in text
    assert "nan_value" in text and "{nan}" in text


def test_bibtex_writer_formats_legacy_provenance_fields() -> None:
    records = {
        "example": {
            "ENTRYTYPE": "article",
            "colrev_origin": ["B", "A;", "A"],
            "colrev_masterdata_provenance": {
                "title": {"source": "db;={value}", "note": "z,a,,b"}
            },
        }
    }

    text = to_string(records, format="bib")

    assert "colrev_origin" in text
    assert (
        "{A;\n                                    A;\n                                    B;}"
        in text
    )
    assert "colrev_masterdata_provenance  = {title:db___value_;a,b,z;}" in text


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


def test_malformed_declared_provenance_mapping_raises_parse_error() -> None:
    text = "@misc{example, provenance={author:source-without-terminator}}"
    with pytest.raises(ParseError, match="Malformed provenance mapping"):
        loads_raw(text, format="bib", mapping_fields=["provenance"])


def test_declared_field_rejects_wrong_legacy_container_format() -> None:
    records = {"example": {"ENTRYTYPE": "misc", "data": ["item"]}}
    text = to_string(records, format="bib", list_fields=["data"])

    with pytest.raises(ParseError, match="Malformed provenance mapping"):
        loads_raw(text, format="bib", mapping_fields=["data"])


def test_provenance_mapping_rejects_arbitrary_nested_values() -> None:
    records = {
        "example": {
            "ENTRYTYPE": "misc",
            "provenance": {
                "author": {"source": "db", "note": "", "nested": {"x": "y"}}
            },
        }
    }
    with pytest.raises(SerializationError):
        to_string(records, format="bib", mapping_fields=["provenance"])


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


def test_raw_file_writer_uses_legacy_mapping_and_list_formats(tmp_path: Path) -> None:
    provenance = {"CURATED": {"source": "github...", "note": ""}}
    origins = ["CROSSREF.bib/001792", "DBLP.bib/001703"]
    records = {
        "example": {
            "ENTRYTYPE": "article",
            "provenance": provenance,
            "colrev_origin": origins,
        }
    }
    path = tmp_path / "raw.bib"

    write(
        records,
        path=path,
        mapping_fields=["provenance"],
        list_fields=["colrev_origin"],
    )

    loaded = load_raw(
        path, mapping_fields=["provenance"], list_fields=["colrev_origin"]
    )
    assert loaded[0]["provenance"] == provenance
    assert loaded[0]["colrev_origin"] == origins


def test_raw_bibtex_preserves_missing_duplicate_and_hash_ids() -> None:
    records = loads_raw(
        "@article{same#key, title={First}}\n@article{same#key, title={Second}}",
        format="bib",
    )
    assert [record.get("ID") for record in records] == ["same#key", "same#key"]
    assert [record["title"] for record in records] == ["First", "Second"]
    assert loads_raw('[{"title": "No ID"}]', format="json")[0].get("ID") is None
