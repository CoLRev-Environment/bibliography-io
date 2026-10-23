"""Tests for RIS loading and writing against repository fixtures."""

import json
from pathlib import Path

from bibliography_io import dumps
from bibliography_io import load_records
from bibliography_io import loads
from bibliography_io import write_records


DATA = Path(__file__).parent / "data" / "ris"


def test_load_ris_fixtures() -> None:
    records = load_records(DATA / "load.ris")
    expected = json.loads((DATA / "load_expected.json").read_text(encoding="utf-8"))
    raw_expected = json.loads(
        (DATA / "load_raw_expected.json").read_text(encoding="utf-8")
    )
    raw_records = load_records(DATA / "load.ris", normalize=False)
    numbered_records = load_records(DATA / "nestedknowledge_numbered_records.ris")

    assert len(records) == len(expected) == 2
    assert records == expected
    assert raw_records == raw_expected
    assert len(numbered_records) == 3
    assert "Activation of peroxisome-proliferator-receptor alpha" in str(
        numbered_records[0]["title"]
    )
    assert numbered_records[2]["author"].startswith("M., Aban")
    assert numbered_records[0]["year"] == "2011-01-01; 2011"
    assert numbered_records[0]["doi"] == "10.1258/ebm.2010.011f01"
    assert numbered_records[2]["abstract"].startswith("PURPOSE:")


def test_ris_new_type_tag_closes_unterminated_record() -> None:
    text = "TY  - JOUR\nTI  - First\nTY  - JOUR\nTI  - Second\nER  -"

    records = loads(text, format="ris")

    assert len(records) == 2
    assert [record["title"] for record in records] == ["First", "Second"]


def test_ris_load_write_round_trip(tmp_path: Path) -> None:
    records = load_records(DATA / "write_expected.bib")
    text = dumps(records, format="ris")
    output = tmp_path / "roundtrip.ris"
    write_records(records, path=output)

    expected = load_records(DATA / "write_expected.ris")
    assert loads(text, format="ris") == expected
    assert load_records(output) == expected


def test_ris_writer_preserves_all_fixture_records(tmp_path: Path) -> None:
    records = load_records(DATA / "load.ris")
    expected = json.loads((DATA / "load_expected.json").read_text(encoding="utf-8"))
    output = tmp_path / "fixture-roundtrip.ris"
    write_records(records, path=output)
    written = load_records(output)
    assert len(written) == len(expected) == len(records)
    for actual, wanted in zip(written, expected):
        for field in ("ID", "ENTRYTYPE", "title", "author"):
            assert actual[field] == wanted[field]


def test_ris_write_file_matches_expected_fixture(tmp_path: Path) -> None:
    records = load_records(DATA / "write_expected.bib")
    output = tmp_path / "written.ris"
    write_records(records, path=output)
    assert loads(output.read_text(encoding="utf-8"), format="ris") == load_records(
        DATA / "write_expected.ris"
    )
