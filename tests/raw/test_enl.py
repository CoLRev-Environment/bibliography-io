"""Tests for ENL loading and writing using repository fixtures."""

from pathlib import Path

from bibliography_io import load_raw, to_string, write


DATA = Path(__file__).parents[1] / "data" / "enl"


def test_enl_load_raw_preserves_source_tags_and_repeated_values() -> None:
    records = load_raw(DATA / "load.enl")

    assert len(records) == 3
    assert records[0]["ENTRYTYPE"] == "article"
    assert records[0]["T"].startswith("How Trust Leads to Commitment")
    assert records[0]["A"] == [
        "Guo, Wenbo",
        "Straub, Detmar W.",
        "Zhang, Pengzhu",
        "Cai, Zhao",
    ]
    assert records[0]["D"] == "2021"


def test_enl_records_write_to_bibtex(tmp_path: Path) -> None:
    records = load_raw(DATA / "load_expected.bib")
    text = to_string(records, format="bib")
    output = tmp_path / "from-enl.bib"
    write(records, path=output)

    assert text.strip() == to_string(records, format="bib").strip()
    assert load_raw(output) == records
