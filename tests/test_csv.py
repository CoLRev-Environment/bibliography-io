"""Tests for CSV file APIs using the retained CSV fixture."""

from pathlib import Path

from bibliography_io import dumps
from bibliography_io import load_records
from bibliography_io import loads
from bibliography_io import write_records


DATA = Path(__file__).parent / "data" / "csv"


def test_load_csv_fixture() -> None:
    records = load_records(DATA / "load.csv")
    expected = load_records(DATA / "load_expected.bib")
    assert len(records) == len(expected) == 2
    assert list(records) == ["1", "2"]
    assert [record["pmid"] for record in records.values()] == ["11223344", "11223345"]
    assert [record["title"] for record in records.values()] == [
        "Paper title",
        "Paper title",
    ]
    assert [record["journal"] for record in records.values()] == ["MISQ", ""]
    assert records["1"]["container_title"] == "Nature"
    assert records["2"]["booktitle"] == ["Nature", "ICIS"]


def test_csv_load_write_round_trip(tmp_path: Path) -> None:
    records = load_records(DATA / "write_expected.bib")
    text = dumps(records, format="csv")
    output = tmp_path / "roundtrip.csv"
    write_records(records, output)

    assert len(loads(text, format="csv")) == len(records)
    assert len(load_records(output)) == len(records)
    assert output.read_text(encoding="utf-8") == (
        DATA / "write_expected.csv"
    ).read_text(encoding="utf-8")


def test_csv_fixture_writes_and_reloads(tmp_path: Path) -> None:
    records = load_records(DATA / "load.csv")
    output = tmp_path / "fixture-roundtrip.csv"
    write_records(records, output)
    written = load_records(output)
    assert len(written) == len(records)
    for before, after in zip(records.values(), written.values()):
        for field in ("pmid", "title", "author", "year", "doi", "pmcid"):
            assert before.get(field) == after.get(field)
