"""Tests for normalized CSV loading."""

from pathlib import Path

from bibliography_io import load
from bibliography_io import write

DATA = Path(__file__).parents[1] / "data" / "csv"


def test_load_csv_fixture() -> None:
    records = load(DATA / "load.csv")
    assert len(records) == 2
    assert list(records) == ["000001", "000002"]
    assert [record["ENTRYTYPE"] for record in records.values()] == [
        "article",
        "inproceedings",
    ]
    assert [record["pmid"] for record in records.values()] == ["11223344", "11223345"]
    assert [record["title"] for record in records.values()] == [
        "Paper title",
        "Paper title",
    ]
    assert records["000001"]["journal"] == "MISQ"
    assert "journal" not in records["000002"]
    assert records["000001"]["journal_book"] == "Nature"
    assert records["000002"]["journal_book"] == "Nature"
    assert records["000002"]["booktitle"] == "ICIS"
    assert records["000001"]["Citation"].startswith("Nature.")
    assert records["000001"]["PMCID"] == "PMC1122334"


def test_csv_fixture_writes_and_reloads(tmp_path: Path) -> None:
    records = load(DATA / "load.csv")
    output = tmp_path / "fixture-roundtrip.csv"
    write(records, path=output)
    written = load(output)

    assert len(written) == len(records)
    for before, after in zip(records.values(), written.values()):
        for field in ("pmid", "title", "author", "year", "doi"):
            assert before.get(field) == after.get(field)
