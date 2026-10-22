"""Tests for source-specific field normalization."""

from bibliography_io import loads
from bibliography_io.normalization import normalize_field_name
from bibliography_io.normalization import normalize_records
from bibliography_io.normalization import normalize_source_record
from bibliography_io.loaders.bibtex import BIBTEX_FIELD_ALIASES
from bibliography_io.loaders.ris import RIS_FIELD_ALIASES


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
    bibtex = loads("@article{sample, journaltitle={Journal}}", format="bib")
    ris = loads("TY  - JOUR\nT1  - Title\nER  -", format="ris")

    assert bibtex[0]["journal"] == "Journal"
    assert ris[0]["title"] == "Title"
