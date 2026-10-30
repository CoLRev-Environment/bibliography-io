"""Tests for normalized CSV loading."""

import json
from pathlib import Path

from bibliography_io import load
from bibliography_io import write

DATA = Path(__file__).parents[1] / "data" / "csv"


def test_load_csv_fixture() -> None:
    records = load(DATA / "load.csv")
    expected = json.loads((DATA / "load_expected.json").read_text(encoding="utf-8"))

    assert len(records) == len(expected) == 2
    assert records == expected
    assert [record.get("ID") for record in records] == [None, None]
    assert [record["pmid"] for record in records] == ["11223344", "11223345"]
    assert [record["title"] for record in records] == ["Paper title", "Paper title"]
    assert records[0]["journal"] == "MISQ"
    assert "journal" not in records[1]
    assert records[0]["container_title"] == "Nature"
    assert records[1]["booktitle"] == "Nature; ICIS"


def test_csv_fixture_writes_and_reloads(tmp_path: Path) -> None:
    records = load(DATA / "load.csv")
    output = tmp_path / "fixture-roundtrip.csv"
    write(records, path=output)
    written = load(output)

    assert len(written) == len(records)
    for before, after in zip(records, written):
        for field in ("pmid", "title", "author", "year", "doi", "pmcid"):
            assert before.get(field) == after.get(field)
