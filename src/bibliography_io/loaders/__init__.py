"""Format-specific loaders that convert input strings to bibliography records."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..exceptions import (
    BackendExecutionError,
    DuplicateRecordIDError,
    MissingRecordIDError,
    OptionalBackendUnavailableError,
    ParseError,
    UnsupportedFormatError,
)


def load_string(
    string: str,
    format: str,
    *,
    normalize: bool = True,
    mapping_fields: frozenset[str] = frozenset(),
    list_fields: frozenset[str] = frozenset(),
    location: str | Path = "<string>",
    header_only: bool = False,
) -> list[dict[str, Any]] | dict[str, dict[str, Any]]:
    """Load text through a format loader, using location for Markdown context."""
    try:
        if format == "bib":
            from .bibtex import load_bibtex

            result = load_bibtex(
                string,
                mapping_fields=mapping_fields,
                list_fields=list_fields,
                normalize=False,
                header_only=header_only,
            )
        elif format == "ris":
            from .ris import load_ris

            result = load_ris(string, normalize=False)
        elif format in {"enl", "nbib", "txt"}:
            from .tagged import load_tagged

            result = load_tagged(string, format=format, normalize=False)
        elif format == "csv":
            from .tabular import load_csv

            result = load_csv(string, normalize=False)
        elif format == "json":
            from .json import load_json

            result = load_json(string, normalize=False)
        elif format == "md":
            from .markdown import load_markdown

            result = load_markdown(string, location=location, normalize=False)
        else:
            raise UnsupportedFormatError(f"Reading {format} is unsupported")
        if not normalize:
            return result
        from .. import _normalize_without_source

        return _normalize_without_source(
            result,
            format_name=format,
            mapping_fields=mapping_fields,
            list_fields=list_fields,
        )
    except (
        BackendExecutionError,
        DuplicateRecordIDError,
        MissingRecordIDError,
        OptionalBackendUnavailableError,
        ParseError,
    ):
        raise
    except Exception as exc:
        raise ParseError(f"Could not load {format} input: {exc}") from exc
    raise UnsupportedFormatError(f"Reading {format} is unsupported")
