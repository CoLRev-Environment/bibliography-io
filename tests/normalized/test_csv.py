"""Tests for normalized CSV loading."""

from pathlib import Path

from bibliography_io import load
from bibliography_io import write

DATA = Path(__file__).parents[1] / "data" / "csv"


def test_load_csv_fixture() -> None:
    records = load(DATA / "load.csv")
    assert len(records) == 2
    assert [record["ID"] for record in records] == ["000001", "000002"]
    assert [record["ENTRYTYPE"] for record in records] == ["article", "inproceedings"]
    assert [record["pmid"] for record in records] == ["11223344", "11223345"]
    assert [record["title"] for record in records] == ["Paper title", "Paper title"]
    assert records[0]["journal"] == "MISQ"
    assert "journal" not in records[1]
    assert records[0]["journal_book"] == "Nature"
    assert records[1]["journal_book"] == "Nature"
    assert records[1]["booktitle"] == "ICIS"
    assert records[0]["Citation"].startswith("Nature.")
    assert records[0]["PMCID"] == "PMC1122334"


def test_csv_fixture_writes_and_reloads(tmp_path: Path) -> None:
    records = load(DATA / "load.csv")
    output = tmp_path / "fixture-roundtrip.csv"
    write(records, path=output)
    written = load(output)

    assert len(written) == len(records)
    for before, after in zip(records, written):
        for field in ("pmid", "title", "author", "year", "doi"):
            assert before.get(field) == after.get(field)
