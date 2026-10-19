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

    assert list(records) == list(expected)
    record = records["1"]
    expected_record = expected["1"]
    assert record["ID"] == expected_record["ID"]
    assert record["ENTRYTYPE"] == expected_record["ENTRYTYPE"]
    for field in ("title", "author", "doi", "number", "issn", "pages"):
        assert record[field] == expected_record[field]
    assert record["volume"] == ["50", "50"]
    assert (
        record["journal_abbreviation"].strip()
        == expected_record["journal_abbreviation"].strip()
    )
    assert record["pubmed_id"] == "12345678"
    assert record["year"] == ["2017", "Mar. 2017"]
    assert record["journal"] == [
        "Secondary Title (journal title, if applicable)",
        "Secondary Title (journal title, if applicable)",
    ]
    assert record["volume"] == ["50", "50"]
    assert (
        record["journal_abbreviation"]
        == "Secondary Title (journal title, if applicable)"
    )
    assert len(numbered_records) == 3
    assert "Activation of peroxisome-proliferator-receptor alpha" in str(
        numbered_records["1"]["title"]
    )
    assert numbered_records["3"]["author"].startswith("M., Aban")
    assert numbered_records["1"]["year"] == ["2011-01-01", "2011", "2011"]
    assert numbered_records["1"]["doi"] == "10.1258/ebm.2010.011f01"
    assert numbered_records["3"]["abstract"].startswith("PURPOSE:")


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
