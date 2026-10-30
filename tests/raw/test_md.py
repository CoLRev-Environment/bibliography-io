"""Tests for Markdown table output and optional reference-list parsing."""

import builtins
from pathlib import Path

import pytest

from bibliography_io import to_string
from bibliography_io import load_raw
from bibliography_io import loads_raw
from bibliography_io import write
from bibliography_io.exceptions import OptionalBackendUnavailableError

DATA = Path(__file__).parents[1] / "data" / "md"


def test_markdown_reference_fixture_requires_optional_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_optional_markdown_dependencies(monkeypatch)
    with pytest.raises(OptionalBackendUnavailableError, match=r"\[markdown\]"):
        load_raw(DATA / "load.md")


def test_markdown_string_requires_optional_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_optional_markdown_dependencies(monkeypatch)
    with pytest.raises(OptionalBackendUnavailableError, match=r"\[markdown\]"):
        loads_raw("A citation", format="md")


def _block_optional_markdown_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = builtins.__import__

    def optional_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "colrev" or name.startswith("colrev."):
            raise ModuleNotFoundError("No module named 'colrev'", name="colrev")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", optional_import)


def test_markdown_loader_uses_registered_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bibliography_io import loads_raw
    from bibliography_io.loaders import markdown

    class FakeBackend:
        @staticmethod
        def loads(text: str, *, source: str) -> list[dict[str, str]]:
            assert text == "A citation"
            assert source == "<string>"
            return [{"ID": "1", "ENTRYTYPE": "article", "title": "Parsed"}]

    class FakeEntryPoint:
        @staticmethod
        def load() -> type[FakeBackend]:
            return FakeBackend

    class FakeEntryPoints:
        @staticmethod
        def select(*, group: str, name: str) -> list[FakeEntryPoint]:
            assert group == "bibliography_io.backends"
            assert name == "markdown"
            return [FakeEntryPoint()]

    monkeypatch.setattr(markdown, "entry_points", FakeEntryPoints)

    assert loads_raw("A citation", format="md") == [
        {"ID": "1", "ENTRYTYPE": "article", "title": "Parsed"}
    ]


def test_markdown_table_write(tmp_path: Path) -> None:
    records = {"one": {"ID": "one", "ENTRYTYPE": "article", "title": "A | sample"}}
    text = to_string(records, format="md")
    assert r"A \| sample" in text

    output = tmp_path / "table.md"
    write(records, path=output)
    assert "| title |" in output.read_text(encoding="utf-8")


def test_markdown_writer_can_preserve_input_field_and_record_order() -> None:
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

    text = to_string(records, format="md", sort_fields=False, sort_by_id=False)

    assert text.splitlines() == [
        "| ID | ENTRYTYPE | title | zeta | alpha |",
        "| --- | --- | --- | --- | --- |",
        "| z | article | Zulu | Z | A |",
        "| a | article | Alpha | z | a |",
    ]
