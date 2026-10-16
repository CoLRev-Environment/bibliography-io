"""Tests for RIS loading and writing against repository fixtures."""

from pathlib import Path

from bibliography_io import dumps
from bibliography_io import load_records
from bibliography_io import loads
from bibliography_io import write_records


DATA = Path(__file__).parent / "data" / "ris"


def test_load_ris_fixtures() -> None:
    records = load_records(DATA / "load.ris")
    expected = load_records(DATA / "load_expected.bib")
    numbered_records = load_records(DATA / "nestedknowledge_numbered_records.ris")

    assert len(records) == 1
    assert len(expected) == 1
    assert (
        next(iter(records.values()))["title"] == next(iter(expected.values()))["title"]
    )
    assert next(iter(records.values()))["doi"] == next(iter(expected.values()))["doi"]
    assert len(numbered_records) == 3
    assert "Activation of peroxisome-proliferator-receptor alpha" in str(
        numbered_records["1"]["title"]
    )


def test_ris_load_write_round_trip(tmp_path: Path) -> None:
    records = load_records(DATA / "write_expected.bib")
    text = dumps(records, format="ris")
    output = tmp_path / "roundtrip.ris"
    write_records(records, output)

    expected = load_records(DATA / "write_expected.ris")
    assert loads(text, format="ris") == expected
    assert load_records(output) == expected


def test_ris_writer_preserves_all_fixture_records(tmp_path: Path) -> None:
    records = load_records(DATA / "load.ris")
    output = tmp_path / "fixture-roundtrip.ris"
    write_records(records, output)
    assert len(load_records(output)) == len(records)


def test_ris_write_file_matches_expected_fixture(tmp_path: Path) -> None:
    records = load_records(DATA / "write_expected.bib")
    output = tmp_path / "written.ris"
    write_records(records, output)
    assert loads(output.read_text(encoding="utf-8"), format="ris") == load_records(
        DATA / "write_expected.ris"
    )
