"""Tests for normalized NBIB loading."""

import json
from pathlib import Path

from bibliography_io import load
from bibliography_io import to_string
from bibliography_io import write

DATA = Path(__file__).parents[1] / "data" / "nbib"


def test_load_nbib_fixture() -> None:
    records = load(DATA / "load.nbib")
    expected = json.loads((DATA / "load_expected.json").read_text(encoding="utf-8"))

    assert records == expected


def test_nbib_load_write_as_bibtex(tmp_path: Path) -> None:
    records = load(DATA / "load.nbib")
    text = to_string(records, format="bib")
    output = tmp_path / "from-nbib.bib"
    write(records, path=output)

    assert "@article" in text
    written = load(output)
    assert len(written) == len(records) == 1
    written_record = {key: value for key, value in written[0].items() if key != "ID"}
    assert written_record == records[0]
