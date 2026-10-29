"""Tests for bibliography_io's standalone public API."""

import subprocess
import sys
from pathlib import Path

import pytest

import bibliography_io as bibio
from bibliography_io import load_raw
from bibliography_io import write


def test_strict_public_api_is_exposed() -> None:
    assert callable(bibio.loads_raw)
    assert callable(bibio.to_string)
    assert callable(load_raw)
    assert callable(write)
    assert callable(bibio.load_primary)
    assert callable(bibio.loads_primary)
    assert callable(bibio.load_raw_df)
    assert callable(bibio.load_primary_df)
    assert callable(bibio.get_nr_records)


def test_package_import_does_not_require_optional_dependencies() -> None:
    source_path = Path(__file__).parents[1] / "src"
    script = """
import sys
sys.path.insert(0, sys.argv[1])
import bibliography_io
records = bibliography_io.loads_raw(
    "@article{sample, title={Standalone}}", format="bib"
)
assert records[0]["title"] == "Standalone"
"""
    subprocess.run(
        [sys.executable, "-S", "-c", script, str(source_path)],
        check=True,
        capture_output=True,
        text=True,
    )


def test_dataframe_apis_report_missing_optional_extra() -> None:
    source_path = Path(__file__).parents[1] / "src"
    script = """
import sys
import tempfile
sys.path.insert(0, sys.argv[1])
from pathlib import Path
import bibliography_io
from bibliography_io.exceptions import OptionalBackendUnavailableError
with tempfile.TemporaryDirectory() as directory:
    source = Path(directory) / "records.bib"
    source.write_text("@article{one, title={One}}", encoding="utf-8")
    for loader in (
        bibliography_io.load_raw_df,
        bibliography_io.load_primary_df,
    ):
        try:
            loader(source)
        except OptionalBackendUnavailableError as exc:
            assert "[excel]" in str(exc)
        else:
            raise AssertionError("pandas extra should be required")
"""
    subprocess.run(
        [sys.executable, "-S", "-c", script, str(source_path)],
        check=True,
        capture_output=True,
        text=True,
    )


def test_excel_write_reports_missing_optional_extra() -> None:
    source_path = Path(__file__).parents[1] / "src"
    script = """
import sys
import tempfile
sys.path.insert(0, sys.argv[1])
from pathlib import Path
from bibliography_io import write
from bibliography_io.exceptions import OptionalBackendUnavailableError
with tempfile.TemporaryDirectory() as directory:
    try:
        write(
            {"one": {"ID": "one", "ENTRYTYPE": "article"}},
            path=Path(directory) / "out.xlsx",
        )
    except OptionalBackendUnavailableError as exc:
        assert "[excel]" in str(exc)
    else:
        raise AssertionError("Excel extra should be required")
"""
    subprocess.run(
        [sys.executable, "-S", "-c", script, str(source_path)],
        check=True,
        capture_output=True,
        text=True,
    )


def test_file_api_round_trip(tmp_path: Path) -> None:
    records = {
        "example2024": {
            "ID": "example2024",
            "ENTRYTYPE": "article",
            "author": "Example, Alex",
            "journal": "Example Journal",
            "title": "An Example",
            "year": "2024",
        }
    }
    source = tmp_path / "input.bib"
    write(records, path=source)
    assert load_raw(source) == list(records.values())


def test_serializers_sort_list_records_by_id_by_default(tmp_path: Path) -> None:
    records = [
        {"ID": "z-last", "ENTRYTYPE": "article", "title": "Last"},
        {"ID": "a-first", "ENTRYTYPE": "article", "title": "First"},
    ]
    original = [record.copy() for record in records]

    text = bibio.to_string(records, format="bib")
    string_output = bibio.write_string(records, "bib")
    output = tmp_path / "sorted.bib"
    write(records, path=output)

    assert [record["ID"] for record in bibio.loads_raw(text, format="bib")] == [
        "a-first",
        "z-last",
    ]
    assert [
        record["ID"] for record in bibio.loads_raw(string_output, format="bib")
    ] == ["a-first", "z-last"]
    assert [record["ID"] for record in load_raw(output)] == ["a-first", "z-last"]
    assert records == original


def test_serializers_can_preserve_list_input_order(tmp_path: Path) -> None:
    records = [
        {"ID": "z-last", "ENTRYTYPE": "article", "title": "Last"},
        {"ID": "a-first", "ENTRYTYPE": "article", "title": "First"},
    ]

    text = bibio.to_string(records, format="bib", sort_by_id=False)
    string_output = bibio.write_string(records, "bib", sort_by_id=False)
    output = tmp_path / "input-order.bib"
    write(records, path=output, sort_by_id=False)

    assert [record["ID"] for record in bibio.loads_raw(text, format="bib")] == [
        "z-last",
        "a-first",
    ]
    assert [
        record["ID"] for record in bibio.loads_raw(string_output, format="bib")
    ] == ["z-last", "a-first"]
    assert [record["ID"] for record in load_raw(output)] == ["z-last", "a-first"]


@pytest.mark.parametrize("sort_by_id", [True, False])
def test_mapping_input_always_preserves_insertion_order(
    tmp_path: Path, sort_by_id: bool
) -> None:
    records = {
        "z-last": {"ID": "z-last", "ENTRYTYPE": "article", "title": "Last"},
        "a-first": {"ID": "a-first", "ENTRYTYPE": "article", "title": "First"},
    }

    text = bibio.to_string(records, format="bib", sort_by_id=sort_by_id)
    string_output = bibio.write_string(records, "bib", sort_by_id=sort_by_id)
    output = tmp_path / f"mapping-{sort_by_id}.bib"
    write(records, path=output, sort_by_id=sort_by_id)

    expected_ids = ["a-first", "z-last"] if sort_by_id else ["z-last", "a-first"]
    assert [record["ID"] for record in bibio.loads_raw(text, format="bib")] == (
        expected_ids
    )
    assert [
        record["ID"] for record in bibio.loads_raw(string_output, format="bib")
    ] == expected_ids
    assert [record["ID"] for record in load_raw(output)] == expected_ids


def test_primary_writer_sorts_mapping_by_id_even_when_sorting_is_disabled(
    tmp_path: Path,
) -> None:
    records = {
        "z-last": {"ID": "z-last", "ENTRYTYPE": "article", "title": "Last"},
        "a-first": {"ID": "a-first", "ENTRYTYPE": "article", "title": "First"},
    }
    output = tmp_path / "primary-sorted.bib"

    write(records, path=output, primary=True, sort_by_id=False)

    assert [record["ID"] for record in load_raw(output)] == ["a-first", "z-last"]


def test_dataframe_helpers_preserve_raw_order_and_primary_ids(tmp_path: Path) -> None:
    pytest.importorskip("pandas")
    source = tmp_path / "records.bib"
    source.write_text(
        "@article{second, title={Second}}\n@book{first, title={First}}",
        encoding="utf-8",
    )

    raw = bibio.load_raw_df(source)
    assert raw.index.tolist() == [0, 1]
    assert raw["ID"].tolist() == ["second", "first"]
    assert raw["title"].tolist() == ["Second", "First"]

    primary = bibio.load_primary_df(source)
    assert primary.index.tolist() == ["second", "first"]
    assert primary.loc["first", "title"] == "First"

    assert bibio.get_nr_records(source) == 2


def test_missing_file_helpers_return_empty_results(tmp_path: Path) -> None:
    missing = tmp_path / "missing.bib"

    assert bibio.load_primary(missing) == {}
    assert bibio.get_nr_records(missing) == 0


def test_loads_primary_empty_text_returns_empty_dictionary() -> None:
    assert bibio.loads_primary("", format="bib") == {}


def test_removed_compatibility_aliases_are_not_exposed() -> None:
    for name in ("load", "write_file", "load_df", "dumps"):
        assert not hasattr(bibio, name)


def test_primary_dict_loads_index_by_id_and_reject_duplicates() -> None:
    records = bibio.loads_primary(
        "@article{one, title={First}}\n@book{two, title={Second}}", format="bib"
    )
    assert list(records) == ["one", "two"]
    assert records["one"]["ENTRYTYPE"] == "article"
    assert records["two"]["title"] == "Second"

    with pytest.raises(bibio.DuplicateRecordIDError):
        bibio.loads_primary(
            "@article{same, title={First}}\n@book{same, title={Second}}", format="bib"
        )

    ris_records = bibio.loads_primary(
        "TY  - JOUR\nID  - ris-one\nTI  - RIS title\nER  -", format="ris"
    )
    assert list(ris_records) == ["ris-one"]
    assert ris_records["ris-one"]["title"] == "RIS title"


def test_primary_dict_header_only_skips_fields(tmp_path: Path) -> None:
    source = tmp_path / "headers.bib"
    source.write_text(
        "@article{one,\n title={A title},\n provenance={not-structured}\n}",
        encoding="utf-8",
    )

    records = bibio.load_primary(
        source, header_only=True, mapping_fields=["provenance"]
    )
    assert records == {"one": {"ID": "one", "ENTRYTYPE": "article"}}


def test_primary_dict_header_only_extracts_record_headers(tmp_path: Path) -> None:
    source = tmp_path / "record-headers.bib"
    source.write_text(
        """@article{one,
 title={A title},
 colrev_origin={source-one; source-two;},
 colrev_status={rev_included},
 file={papers/one.pdf},
 screening_criteria={include},
 colrev_masterdata_provenance={title:database;imported;},
 abstract={ignored payload}
}""",
        encoding="utf-8",
    )

    records = bibio.load_primary(
        source,
        header_only=True,
        mapping_fields=["colrev_masterdata_provenance"],
        list_fields=["colrev_origin"],
    )

    assert records == {
        "one": {
            "ID": "one",
            "ENTRYTYPE": "article",
            "colrev_origin": ["source-one", "source-two"],
            "colrev_status": "rev_included",
            "file": "papers/one.pdf",
            "screening_criteria": "include",
            "colrev_masterdata_provenance": {
                "title": {"source": "database", "note": "imported"}
            },
        }
    }


def test_primary_dict_writer_validates_ids_and_round_trips_structured_fields(
    tmp_path: Path,
) -> None:
    records = {
        "one": {
            "ID": "one",
            "ENTRYTYPE": "article",
            "provenance": {"CURATED": {"source": "database", "note": ""}},
        }
    }
    output = tmp_path / "primary.bib"
    write(records, path=output, primary=True, mapping_fields=["provenance"])
    assert bibio.load_primary(output, mapping_fields=["provenance"]) == records

    with pytest.raises(bibio.MissingRecordIDError):
        write({"one": {"ENTRYTYPE": "article"}}, path=output, primary=True)
    with pytest.raises(bibio.DuplicateRecordIDError):
        write(
            {
                "first": {"ID": "same", "ENTRYTYPE": "article"},
                "second": {"ID": "same", "ENTRYTYPE": "book"},
            },
            path=output,
            primary=True,
        )
    with pytest.raises(bibio.UnsupportedFormatError):
        write(records, path=tmp_path / "primary.ris", primary=True)
    with pytest.raises(bibio.RecordValidationError, match="mapping of IDs"):
        write([{"ID": "one", "ENTRYTYPE": "article"}], path=output, primary=True)


def test_writer_omits_empty_mapping_fields_for_primary_and_raw_records(
    tmp_path: Path,
) -> None:
    records = {
        "one": {
            "ID": "one",
            "ENTRYTYPE": "article",
            "empty_provenance": {},
            "provenance": {"CURATED": {"source": "database", "note": ""}},
        }
    }
    primary_output = tmp_path / "primary.bib"
    raw_output = tmp_path / "raw.bib"

    write(
        records,
        path=primary_output,
        primary=True,
        mapping_fields=["empty_provenance", "provenance"],
    )
    write(
        records,
        path=raw_output,
        mapping_fields=["empty_provenance", "provenance"],
    )

    primary_text = primary_output.read_text(encoding="utf-8")
    raw_text = raw_output.read_text(encoding="utf-8")
    assert "empty_provenance" not in primary_text
    assert "   provenance" in primary_text
    assert "empty_provenance" not in raw_text


def test_primary_writer_and_raw_writer_sort_ids_by_default(
    tmp_path: Path,
) -> None:
    records = {
        "z-last": {"ID": "z-last", "ENTRYTYPE": "article", "title": "Last"},
        "a-first": {"ID": "a-first", "ENTRYTYPE": "article", "title": "First"},
    }
    primary_path = tmp_path / "primary.bib"
    raw_path = tmp_path / "raw.bib"

    write(records, path=primary_path, primary=True)
    write(records, path=raw_path)

    assert list(bibio.load_primary(primary_path)) == ["a-first", "z-last"]
    assert [record["ID"] for record in load_raw(raw_path)] == ["a-first", "z-last"]
    assert "   title                         = {Last}," in primary_path.read_text(
        encoding="utf-8"
    )


def test_write_requires_keyword_path(tmp_path: Path) -> None:
    records = {"example": {"ID": "example", "ENTRYTYPE": "article"}}
    output = tmp_path / "example.bib"

    write(records, path=output)
    assert output.is_file()

    try:
        write(records, output)
    except TypeError:
        pass
    else:
        raise AssertionError("write must reject a positional path")


def test_bibtex_and_ris_round_trip(tmp_path: Path) -> None:
    records = load_raw(Path(__file__).parent / "data" / "bib" / "write_expected.bib")

    bib_path = tmp_path / "roundtrip.bib"
    write(records, path=bib_path)
    assert load_raw(bib_path) == records

    ris_path = tmp_path / "roundtrip.ris"
    write(records, path=ris_path)
    ris_records = load_raw(ris_path)
    ris_record = next(iter(ris_records))
    source_record = next(iter(records))
    assert ris_record["title"] == source_record["title"]
    assert ris_record["author"] == source_record["author"]
    assert ris_record["doi"] == source_record["doi"]
