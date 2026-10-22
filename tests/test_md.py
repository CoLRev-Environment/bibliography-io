"""Tests for Markdown table output and optional reference-list parsing."""

import builtins
import sys
from pathlib import Path
from types import ModuleType

import pytest

from bibliography_io import dumps
from bibliography_io import load_records
from bibliography_io import write_records
from bibliography_io.exceptions import OptionalBackendUnavailableError

DATA = Path(__file__).parent / "data" / "md"


def test_markdown_reference_fixture_requires_optional_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_optional_markdown_dependencies(monkeypatch)
    with pytest.raises(OptionalBackendUnavailableError, match=r"\[markdown\]"):
        load_records(DATA / "load.md")


def test_markdown_string_requires_optional_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_optional_markdown_dependencies(monkeypatch)
    from bibliography_io import loads

    with pytest.raises(OptionalBackendUnavailableError, match=r"\[markdown\]"):
        loads("A citation", format="md")


def _block_optional_markdown_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = builtins.__import__

    def optional_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "colrev" or name.startswith("colrev."):
            raise ModuleNotFoundError("No module named 'colrev'", name="colrev")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", optional_import)


def test_markdown_backend_adapts_legacy_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    module = ModuleType("bibliography_io.loader.md")

    class FakeMarkdownLoader:
        def __init__(self, *, filename: Path, logger: object) -> None:
            self.filename = filename

        def load_records_list(self) -> list[dict[str, str]]:
            assert self.filename.read_text(encoding="utf-8") == "A citation"
            return [{"ID": "1", "ENTRYTYPE": "article", "title": "Parsed"}]

    module.MarkdownLoader = FakeMarkdownLoader  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "bibliography_io.loader.md", module)

    from bibliography_io.markdown_backend import loads

    assert loads("A citation", source="<string>") == [
        {"ID": "1", "ENTRYTYPE": "article", "title": "Parsed"}
    ]


def test_markdown_table_write(tmp_path: Path) -> None:
    records = {"one": {"ID": "one", "ENTRYTYPE": "article", "title": "A | sample"}}
    text = dumps(records, format="md")
    assert r"A \| sample" in text

    output = tmp_path / "table.md"
    write_records(records, path=output)
    assert "| title |" in output.read_text(encoding="utf-8")
