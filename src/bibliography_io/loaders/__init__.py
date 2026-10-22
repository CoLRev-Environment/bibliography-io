"""Format-specific loaders that convert input text to bibliography records."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..exceptions import BackendExecutionError
from ..exceptions import OptionalBackendUnavailableError
from ..exceptions import ParseError
from ..exceptions import UnsupportedFormatError


def load_text(
    text: str,
    fmt: str,
    *,
    mapping_fields: frozenset[str] = frozenset(),
    list_fields: frozenset[str] = frozenset(),
    source: str | Path = "<string>",
) -> list[dict[str, Any]]:
    """Load records from text by dispatching to the format-specific loader."""
    try:
        if fmt == "bib":
            from .bibtex import load_bibtex

            return load_bibtex(
                text, mapping_fields=mapping_fields, list_fields=list_fields
            )
        if fmt == "ris":
            from .ris import load_ris

            return load_ris(text)
        if fmt in {"enl", "nbib", "txt"}:
            from .tagged import load_tagged

            return load_tagged(text, fmt)
        if fmt == "csv":
            from .tabular import load_csv

            return load_csv(text)
        if fmt == "json":
            from .json import load_json

            return load_json(text)
        if fmt == "md":
            from .markdown import load_markdown

            return load_markdown(text, source=source)
    except (BackendExecutionError, OptionalBackendUnavailableError, ParseError):
        raise
    except Exception as exc:
        raise ParseError(f"Could not load {fmt} input: {exc}") from exc
    raise UnsupportedFormatError(f"Reading {fmt} is unsupported")
