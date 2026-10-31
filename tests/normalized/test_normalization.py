"""Tests for source-specific field normalization."""

from pathlib import Path

import pytest

from bibliography_io import MissingRecordIDError, get_nr_records, load, load_df
from bibliography_io import loads, loads_raw, write_string
from bibliography_io.loaders import load_string
from bibliography_io.loaders.bibtex import BIBTEX_FIELD_ALIASES
from bibliography_io.loaders.ris import RIS_FIELD_ALIASES
from bibliography_io.normalization import normalize_field_name
from bibliography_io.normalization import normalize_records
from bibliography_io.normalization import normalize_source_record
from bibliography_io.writers.csv import write_csv


def test_field_aliases_are_source_specific_and_opt_in() -> None:
    assert normalize_field_name("T1") == "t1"
    assert (
        normalize_field_name("colrev.vendor.identifier") == "colrev_vendor_identifier"
    )
    assert normalize_field_name("colrev.vendor.identifier", preserve_dots=True) == (
        "colrev.vendor.identifier"
    )
    assert (
        normalize_field_name(
            "colrev.web_of_science.unique-id",
            preserve_dots=True,
            preserve_dashes=True,
        )
        == "colrev.web_of_science.unique-id"
    )
    assert normalize_field_name("article-number") == "article_number"
    assert normalize_field_name("T1", field_aliases=RIS_FIELD_ALIASES) == "title"
    assert normalize_source_record({"journaltitle": "Journal"}) == {
        "journaltitle": "Journal"
    }
    assert normalize_source_record(
        {"journaltitle": "Journal"}, field_aliases=BIBTEX_FIELD_ALIASES
    ) == {"journal": "Journal"}
    assert normalize_source_record(
        {"colrev.web_of_science.unique-id": "WOS:123"}, format="bib"
    ) == {"colrev.web_of_science.unique-id": "WOS:123"}
    assert normalize_source_record(
        {"colrev.pubmed.pubmedid": "12345"}, format="csv"
    ) == {"colrev.pubmed.pubmedid": "12345"}


def test_normalize_records_accepts_explicit_field_aliases() -> None:
    records = normalize_records(
        [{"ID": "one", "authors": "Ada Smith"}],
        field_aliases={"authors": "author"},
    )
    assert records["one"]["author"] == "Ada Smith"
    assert "authors" not in records["one"]


def test_generic_normalization_preserves_unknown_names_and_skips_inference() -> None:
    assert normalize_source_record(
        {"Custom Field": "value", "authors": "Ada", "journal_book": "Venue"},
        field_aliases={"authors": "author"},
        generic_normalization=True,
    ) == {
        "Custom Field": "value",
        "author": "Ada",
        "journal_book": "Venue",
    }
    assert normalize_source_record({"Custom Field": "value"}) == {
        "custom_field": "value"
    }


def test_writer_does_not_apply_generic_normalization() -> None:
    output = write_string(
        {
            "example": {
                "ID": "example",
                "ENTRYTYPE": "misc",
                "Custom Field": "value",
            }
        },
        "csv",
    )

    assert output.splitlines()[0] == "ID,ENTRYTYPE,custom_field"


def test_loaders_apply_their_own_field_aliases() -> None:
    bibtex = load_string(
        """\
@article{sample,
  journaltitle={Journal},
}""",
        format="bib",
        normalize=True,
    )
    ris = load_string("TY  - JOUR\nT1  - Title\nER  -", format="ris", normalize=True)

    assert bibtex["sample"]["journal"] == "Journal"
    assert ris["000001"]["title"] == "Title"


def test_generic_bibtex_load_preserves_namespaced_and_unknown_field_names(
    tmp_path: Path,
) -> None:
    text = """\
@article{example,
  colrev.google_scholar.uid={GS:123},
  colrev.files_dir.note={checked},
  custom-field={custom value},
}"""
    source = tmp_path / "records.bib"
    source.write_text(text, encoding="utf-8")

    expected = {
        "example": {
            "ID": "example",
            "ENTRYTYPE": "article",
            "colrev.google_scholar.uid": "GS:123",
            "colrev.files_dir.note": "checked",
            "custom-field": "custom value",
        }
    }

    assert load(source) == expected
    assert loads(text, format="bib") == expected


def test_json_load_normalizes_multivalued_fields_by_default() -> None:
    text = """[
      {
        "ENTRYTYPE": "article",
        "ID": "sample",
        "author": ["Ada", "Ada", "Grace"],
        "keywords": ["logic", "logic", "computing"],
        "journal": ["Journal", "Journal", ""],
        "volume": ["", "4", "4"],
        "year": ["2020", "2021"],
        "empty": ["", null]
      }
    ]"""

    assert load_string(text, format="json", normalize=True) == {
        "sample": {
            "ENTRYTYPE": "article",
            "ID": "sample",
            "author": "Ada and Grace",
            "keywords": "logic; computing",
            "journal": "Journal",
            "volume": "4",
            "year": "2020; 2021",
        }
    }


def test_non_normalized_json_preserves_source_values() -> None:
    text = '[{"ENTRYTYPE":"article","authors":["Ada","Grace"],"volume":["4","4"]}]'

    assert loads_raw(text, format="json") == [
        {
            "ENTRYTYPE": "article",
            "authors": ["Ada", "Grace"],
            "volume": ["4", "4"],
        }
    ]


def test_json_authors_are_standardized_and_joined_with_and() -> None:
    text = '[{"ID":"sample","authors":["Ada", "Grace"]}]'

    assert load_string(text, format="json", normalize=True) == {
        "sample": {"ID": "sample", "author": "Ada and Grace", "ENTRYTYPE": "misc"}
    }
    assert loads_raw(text, format="json") == [
        {"ID": "sample", "authors": ["Ada", "Grace"]}
    ]


def test_internal_dispatchers_accept_format_keyword() -> None:
    parsed = load_string(
        '[{"ID":"sample","ENTRYTYPE":"misc","title":"Example"}]',
        format="json",
    )
    with pytest.raises(MissingRecordIDError):
        load_string("PT  - JOUR\nTI  - Example\n", format="nbib")
    written = write_csv(
        {"example": {"ID": "example", "ENTRYTYPE": "misc", "title": "Example"}}
    )

    assert parsed["sample"]["title"] == "Example"
    assert written.splitlines()[0] == "ID,ENTRYTYPE,title"


def test_load_df_preserves_normalized_record_order(tmp_path: Path) -> None:
    pytest.importorskip("pandas")

    source = tmp_path / "records.bib"
    source.write_text(
        """\
@article{second,
  title={Second},
}
@book{first,
  title={First},
}""",
        encoding="utf-8",
    )

    records = load_df(source)

    assert records.index.tolist() == ["second", "first"]
    assert records["ID"].tolist() == ["second", "first"]
    assert records["title"].tolist() == ["Second", "First"]
    assert get_nr_records(source) == 2
