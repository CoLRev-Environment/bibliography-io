"""Tests for ENL loading and writing using repository fixtures."""

from pathlib import Path

from bibliography_io import to_string
from bibliography_io import load_raw
from bibliography_io import write


DATA = Path(__file__).parents[1] / "data" / "enl"


def test_enl_records_write_to_bibtex(tmp_path: Path) -> None:
    records = load_raw(DATA / "load_expected.bib")
    text = to_string(records, format="bib")
    output = tmp_path / "from-enl.bib"
    write(records, path=output)

    assert text.strip() == to_string(records, format="bib").strip()
    assert load_raw(output) == records
