"""Tests for Markdown table output and optional reference-list parsing."""

from __future__ import annotations

import builtins
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from bibliography_io import load, load_raw, loads, loads_raw, to_string, write

DATA = Path(__file__).parents[1] / "data" / "md"


def test_markdown_reference_fixture_requires_optional_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_optional_markdown_dependencies(monkeypatch)
    from bibliography_io import exceptions

    with pytest.raises(
        exceptions.OptionalBackendUnavailableError, match=r"\[markdown\]"
    ):
        load_raw(DATA / "load.md")


def test_markdown_string_requires_optional_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_optional_markdown_dependencies(monkeypatch)
    from bibliography_io import exceptions

    with pytest.raises(
        exceptions.OptionalBackendUnavailableError, match=r"\[markdown\]"
    ):
        loads_raw("A citation", format="md")


def _block_optional_markdown_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = builtins.__import__

    def optional_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "grobid_tei" or name.startswith("grobid_tei."):
            raise ModuleNotFoundError("No module named 'grobid_tei'", name="grobid_tei")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", optional_import)


def _install_fake_grobid(
    monkeypatch: pytest.MonkeyPatch,
    *,
    references: list[SimpleNamespace],
    calls: dict[str, object],
    failure: Exception | None = None,
) -> None:
    class FakeGrobidClient:
        def __init__(self, *, service_url: str) -> None:
            calls["service_url"] = service_url

        def process_citation_list(
            self, citations: list[str], *, consolidate_citations: bool = False
        ) -> bytes:
            calls["citations"] = citations
            calls["consolidate_citations"] = consolidate_citations
            if failure is not None:
                raise failure
            return b"<TEI/>"

    class FakeTEIDocument:
        @classmethod
        def from_bytes(cls, xml: bytes) -> FakeTEIDocument:
            calls["tei_xml"] = xml
            return cls()

        def references(self) -> list[SimpleNamespace]:
            return references

    module = ModuleType("grobid_tei")
    module.GrobidClient = FakeGrobidClient
    module.TEIDocument = FakeTEIDocument
    monkeypatch.setitem(sys.modules, "grobid_tei", module)


def _disable_registered_markdown_backends(monkeypatch: pytest.MonkeyPatch) -> None:
    from bibliography_io.loaders import markdown

    class EmptyEntryPoints:
        @staticmethod
        def select(*, group: str, name: str) -> list[object]:
            assert group == "bibliography_io.backends"
            assert name == "markdown"
            return []

    monkeypatch.setattr(markdown, "entry_points", EmptyEntryPoints)


def test_markdown_loader_uses_registered_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bibliography_io import loads_raw
    from bibliography_io.loaders import markdown

    locations: list[str | Path] = []

    class FakeBackend:
        @staticmethod
        def loads(text: str, *, source: str | Path) -> list[dict[str, str]]:
            assert text == "A citation"
            locations.append(source)
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

    source = tmp_path / "references.md"
    source.write_text("A citation", encoding="utf-8")
    assert load(source) == {"1": {"ID": "1", "ENTRYTYPE": "article", "title": "Parsed"}}
    assert locations == ["<string>", source]


@pytest.mark.parametrize(
    ("environment_url", "expected_url"),
    [
        (None, "http://localhost:8070"),
        ("https://grobid.example:8071", "https://grobid.example:8071"),
    ],
)
def test_markdown_loader_uses_grobid_tei(
    monkeypatch: pytest.MonkeyPatch,
    environment_url: str | None,
    expected_url: str,
) -> None:
    _disable_registered_markdown_backends(monkeypatch)
    if environment_url is None:
        monkeypatch.delenv("BIBLIOGRAPHY_IO_GROBID_URL", raising=False)
    else:
        monkeypatch.setenv("BIBLIOGRAPHY_IO_GROBID_URL", environment_url)

    calls: dict[str, object] = {}
    _install_fake_grobid(
        monkeypatch,
        calls=calls,
        references=[
            SimpleNamespace(
                fields={
                    "entrytype": "article",
                    "title": "First title",
                    "author": "First Author",
                },
                tei_id="b0",
            ),
            SimpleNamespace(
                fields={"entrytype": "book", "title": "Second title"},
                tei_id="b1",
            ),
        ],
    )
    text = "# References\n\nFirst citation\n  ## Notes\nSecond citation\n"

    records = loads_raw(text, format="md")

    assert calls == {
        "service_url": expected_url,
        "citations": ["First citation", "Second citation"],
        "consolidate_citations": False,
        "tei_xml": b"<TEI/>",
    }
    assert records == [
        {
            "ID": "1",
            "ENTRYTYPE": "article",
            "title": "First title",
            "author": "First Author",
        },
        {"ID": "2", "ENTRYTYPE": "book", "title": "Second title"},
    ]

    normalized = loads(text, format="md")
    assert list(normalized) == ["1", "2"]
    assert normalized["1"]["title"] == "First title"


def test_markdown_loader_works_without_colrev_and_does_not_manage_grobid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_import = builtins.__import__

    def import_without_colrev(name: str, *args: object, **kwargs: object) -> object:
        if name == "colrev" or name.startswith("colrev."):
            raise ModuleNotFoundError("No module named 'colrev'", name="colrev")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_colrev)
    _disable_registered_markdown_backends(monkeypatch)
    monkeypatch.setenv("BIBLIOGRAPHY_IO_GROBID_URL", "http://caller.example:8070")

    calls: dict[str, object] = {}
    _install_fake_grobid(
        monkeypatch,
        calls=calls,
        references=[SimpleNamespace(fields={"entrytype": "misc", "title": "Parsed"})],
    )

    from bibliography_io import loads_raw
    from bibliography_io.loaders.markdown import load_markdown

    assert load_markdown("A citation", location="<string>", normalize=False) == [
        {"ID": "1", "ENTRYTYPE": "misc", "title": "Parsed"}
    ]
    assert calls["service_url"] == "http://caller.example:8070"
    assert calls["citations"] == ["A citation"]
    assert loads_raw("Another citation", format="md")[0]["title"] == "Parsed"
    assert calls["service_url"] == "http://caller.example:8070"


def test_markdown_grobid_failure_is_wrapped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bibliography_io import exceptions

    _disable_registered_markdown_backends(monkeypatch)
    _install_fake_grobid(
        monkeypatch,
        calls={},
        references=[],
        failure=RuntimeError("service unavailable"),
    )

    with pytest.raises(
        exceptions.BackendExecutionError,
        match="GROBID service is running and reachable",
    ) as error:
        loads_raw("A citation", format="md")

    assert isinstance(error.value.__cause__, RuntimeError)


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
