"""Tests for CSV file APIs using the retained CSV fixture."""

import csv
from io import StringIO
from pathlib import Path

from bibliography_io import to_string
from bibliography_io import load_raw
from bibliography_io import loads_raw
from bibliography_io import write
from bibliography_io.writers.csv import write_csv


DATA = Path(__file__).parents[1] / "data" / "csv"


def test_csv_load_write_round_trip(tmp_path: Path) -> None:
    records = load_raw(DATA / "write_expected.bib")
    text = to_string(records, format="csv")
    output = tmp_path / "roundtrip.csv"
    write(records, path=output)

    assert len(loads_raw(text, format="csv")) == len(records)
    assert len(load_raw(output)) == len(records)
    assert output.read_text(encoding="utf-8") == (
        DATA / "write_expected.csv"
    ).read_text(encoding="utf-8")


def test_csv_table_writer_uses_legacy_columns_and_sorts_rows() -> None:
    records = {
        "z": {
            "ID": "z",
            "ENTRYTYPE": "article",
            "title": "Zulu",
            "z_extra": "last",
            "a_extra": "",
            "empty": None,
        },
        "a": {
            "ID": "a",
            "ENTRYTYPE": "book",
            "title": "Alpha",
            "z_extra": "first",
            "a_extra": "",
            "empty": "",
        },
    }

    rows = list(csv.reader(StringIO(write_csv(records))))

    assert rows == [
        ["ID", "ENTRYTYPE", "title", "z_extra"],
        ["a", "book", "Alpha", "first"],
        ["z", "article", "Zulu", "last"],
    ]


def test_csv_writer_can_preserve_input_field_and_record_order() -> None:
    records = {
        "z": {
            "ID": "z",
            "ENTRYTYPE": "article",
            "title": "Zulu",
            "zeta": "Z",
            "alpha": "A",
        },
        "a": {
            "ID": "a",
            "ENTRYTYPE": "article",
            "title": "Alpha",
            "alpha": "a",
            "zeta": "z",
        },
    }

    rows = list(
        csv.reader(StringIO(write_csv(records, sort_fields=False, sort_by_id=False)))
    )

    assert rows == [
        ["ID", "ENTRYTYPE", "title", "zeta", "alpha"],
        ["z", "article", "Zulu", "Z", "A"],
        ["a", "article", "Alpha", "z", "a"],
    ]
