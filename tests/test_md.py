"""Tests for Markdown table output and optional reference-list parsing."""

from pathlib import Path

import pytest

from bibliography_io import dumps
from bibliography_io import load_records
from bibliography_io import write_records
from bibliography_io.exceptions import OptionalBackendUnavailableError


DATA = Path(__file__).parent / "data" / "md"


def test_markdown_reference_fixture_requires_optional_backend() -> None:
    with pytest.raises(OptionalBackendUnavailableError):
        load_records(DATA / "load.md")


def test_markdown_table_write(tmp_path: Path) -> None:
    records = {"one": {"ID": "one", "ENTRYTYPE": "article", "title": "A | sample"}}
    text = dumps(records, format="md")
    assert r"A \| sample" in text

    output = tmp_path / "table.md"
    write_records(records, path=output)
    assert "| title |" in output.read_text(encoding="utf-8")
