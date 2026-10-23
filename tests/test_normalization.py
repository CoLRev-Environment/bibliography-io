"""Tests for source-specific field normalization."""

from bibliography_io import loads_raw
from bibliography_io.normalization import normalize_field_name
from bibliography_io.normalization import normalize_records
from bibliography_io.normalization import normalize_source_record
from bibliography_io.loaders.bibtex import BIBTEX_FIELD_ALIASES
from bibliography_io.loaders import load_string
from bibliography_io.loaders.ris import RIS_FIELD_ALIASES
from bibliography_io.writers.tabular import write_table


def test_field_aliases_are_source_specific_and_opt_in() -> None:
    assert normalize_field_name("T1") == "t1"
    assert normalize_field_name("T1", field_aliases=RIS_FIELD_ALIASES) == "title"
    assert normalize_source_record({"journaltitle": "Journal"}) == {
        "journaltitle": "Journal"
    }
    assert normalize_source_record(
        {"journaltitle": "Journal"}, field_aliases=BIBTEX_FIELD_ALIASES
    ) == {"journal": "Journal"}


def test_normalize_records_accepts_explicit_field_aliases() -> None:
    records = normalize_records(
        [{"ID": "one", "authors": "Ada Smith"}],
        field_aliases={"authors": "author"},
    )
    assert records["one"]["author"] == "Ada Smith"
    assert "authors" not in records["one"]


def test_loaders_apply_their_own_field_aliases() -> None:
    bibtex = loads_raw("@article{sample, journaltitle={Journal}}", format="bib")
    ris = loads_raw("TY  - JOUR\nT1  - Title\nER  -", format="ris")

    assert bibtex[0]["journal"] == "Journal"
    assert ris[0]["title"] == "Title"


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

    assert loads_raw(text, format="json") == [
        {
            "ENTRYTYPE": "article",
            "ID": "sample",
            "author": "Ada and Grace",
            "keywords": "logic; computing",
            "journal": "Journal",
            "volume": "4",
            "year": "2020; 2021",
        }
    ]


def test_non_normalized_json_preserves_source_values() -> None:
    text = '[{"ENTRYTYPE":"article","authors":["Ada","Grace"],"volume":["4","4"]}]'

    assert loads_raw(text, format="json", normalize=False) == [
        {
            "ENTRYTYPE": "article",
            "authors": ["Ada", "Grace"],
            "volume": ["4", "4"],
        }
    ]


def test_internal_dispatchers_accept_format_keyword() -> None:
    parsed = load_string('[{"ENTRYTYPE":"misc","title":"Example"}]', format="json")
    tagged = load_string("PT  - JOUR\nTI  - Example\n", format="nbib")
    written = write_table(
        {"example": {"ID": "example", "ENTRYTYPE": "misc", "title": "Example"}},
        format="csv",
    )

    assert parsed[0]["title"] == "Example"
    assert tagged[0]["ENTRYTYPE"] == "article"
    assert written.splitlines()[0] == "ID,ENTRYTYPE,title"
