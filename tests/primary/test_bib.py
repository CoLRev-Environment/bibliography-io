"""Tests for the BibTeX-only primary-record API."""

from pathlib import Path

import pytest

import bibliography_io as bibio
from bibliography_io import write


def test_primary_dict_loads_index_by_id_and_reject_duplicates() -> None:
    records = bibio.loads_primary(
        "@article{one, title={First}}\n@book{two, title={Second}}", format="bib"
    )
    assert list(records) == ["one", "two"]
    assert records["one"]["ENTRYTYPE"] == "article"
    assert records["two"]["title"] == "Second"

    with pytest.raises(bibio.DuplicateRecordIDError):
        bibio.loads_primary(
            "@article{same, title={First}}\n@book{same, title={Second}}",
            format="bib",
        )


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


def test_primary_writer_validates_ids_and_round_trips_structured_fields(
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


def test_primary_writer_sorts_ids_by_default(tmp_path: Path) -> None:
    records = {
        "z-last": {"ID": "z-last", "ENTRYTYPE": "article", "title": "Last"},
        "a-first": {"ID": "a-first", "ENTRYTYPE": "article", "title": "First"},
    }
    output = tmp_path / "primary.bib"

    write(records, path=output, primary=True)

    assert list(bibio.load_primary(output)) == ["a-first", "z-last"]


def test_primary_writer_sorts_mapping_by_id_when_sorting_is_disabled(
    tmp_path: Path,
) -> None:
    records = {
        "z-last": {"ID": "z-last", "ENTRYTYPE": "article", "title": "Last"},
        "a-first": {"ID": "a-first", "ENTRYTYPE": "article", "title": "First"},
    }
    output = tmp_path / "primary-sorted.bib"

    write(records, path=output, primary=True, sort_by_id=False)

    assert [record["ID"] for record in bibio.load_primary(output).values()] == [
        "a-first",
        "z-last",
    ]


def test_load_primary_empty_and_missing_files(tmp_path: Path) -> None:
    assert bibio.loads_primary("", format="bib") == {}
    assert bibio.load_primary(tmp_path / "missing.bib") == {}


def test_primary_undeclared_native_values_are_strings(tmp_path: Path) -> None:
    source = tmp_path / "primary.json"
    source.write_text(
        '[{"ID":"one","ENTRYTYPE":"article","title":42,"metadata":{"rank":2}}]',
        encoding="utf-8",
    )

    records = bibio.load_primary(source)

    assert records == {
        "one": {
            "ID": "one",
            "ENTRYTYPE": "article",
            "title": "42",
            "metadata": "{'rank': 2}",
        }
    }


def test_primary_dataframe_is_indexed_by_record_id(tmp_path: Path) -> None:
    pytest.importorskip("pandas")
    source = tmp_path / "records.bib"
    source.write_text(
        "@article{second, title={Second}}\n@book{first, title={First}}",
        encoding="utf-8",
    )

    records = bibio.load_primary_df(source)

    assert records.index.tolist() == ["second", "first"]
    assert records.loc["first", "title"] == "First"


def test_primary_writer_omits_empty_mappings_and_sorts_ids(tmp_path: Path) -> None:
    records = {
        "z-last": {
            "ID": "z-last",
            "ENTRYTYPE": "article",
            "title": "Last",
            "empty_provenance": {},
            "provenance": {"CURATED": {"source": "database", "note": ""}},
        },
        "a-first": {"ID": "a-first", "ENTRYTYPE": "article", "title": "First"},
    }
    output = tmp_path / "primary.bib"

    write(
        records,
        path=output,
        primary=True,
        mapping_fields=["empty_provenance", "provenance"],
    )

    text = output.read_text(encoding="utf-8")
    assert "empty_provenance" not in text
    assert "   provenance" in text
    assert list(bibio.load_primary(output)) == ["a-first", "z-last"]
