"""Tests for normalized RIS loading."""

from pathlib import Path

from bibliography_io import load
from bibliography_io import loads
from bibliography_io import load_raw
from bibliography_io import write
from bibliography_io.loaders.ris import load_ris

DATA = Path(__file__).parents[1] / "data" / "ris"


def test_load_ris_fixtures() -> None:
    records = load(DATA / "load.ris")
    assert [record["ID"] for record in records] == ["000001", "000002"]
    assert records[0]["ENTRYTYPE"] == "inproceedings"
    assert records[0]["booktitle"].startswith("Secondary Title")
    assert records[0]["author"].count(" and ") == 4
    assert records[1]["journal"].startswith("Secondary Title")


def test_ris_type_tag_normalizes_to_bibtex_entry_type() -> None:
    text = "TY  - CONF\nID  - conf-one\nTI  - Conference paper\nER  -"

    assert loads(text, format="ris") == [
        {
            "ENTRYTYPE": "inproceedings",
            "ID": "000001",
            "title": "Conference paper",
        }
    ]
    assert load_ris("TY  - CONF\nTI  - Conference paper\nER  -", normalize=True) == [
        {"ENTRYTYPE": "inproceedings", "ID": "000001", "title": "Conference paper"}
    ]


def test_numbered_ris_fixture_is_normalized() -> None:
    records = load(DATA / "nestedknowledge_numbered_records.ris")

    assert len(records) == 3
    assert "Activation of peroxisome-proliferator-receptor alpha" in str(
        records[0]["title"]
    )
    assert records[2]["author"].startswith("M., Aban")
    assert records[0]["year"] == "2011"
    assert records[0]["doi"] == "10.1258/ebm.2010.011f01"
    assert records[2]["abstract"].startswith("PURPOSE:")


def test_loads_ris_text_returns_normalized_records() -> None:
    assert loads("TY  - JOUR\nTI  - A title\nER  -", format="ris") == [
        {"ENTRYTYPE": "article", "ID": "000001", "title": "A title"}
    ]


def test_ris_load_write_round_trip(tmp_path: Path) -> None:
    records = load_raw(DATA / "write_expected.bib")
    output = tmp_path / "roundtrip.ris"
    write(records, path=output)

    expected = load(DATA / "write_expected.ris")
    assert load(output) == expected


def test_ris_writer_preserves_all_fixture_records(tmp_path: Path) -> None:
    records = load(DATA / "load.ris")
    output = tmp_path / "fixture-roundtrip.ris"
    write(records, path=output)
    written = load(output)

    assert len(written) == len(records) == 2
    for actual, wanted in zip(written, records):
        for field in ("ID", "ENTRYTYPE", "title", "author"):
            assert actual[field] == wanted[field]
