"""Format-specific loaders that convert input strings to bibliography records."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..exceptions import BackendExecutionError
from ..exceptions import OptionalBackendUnavailableError
from ..exceptions import ParseError
from ..exceptions import UnsupportedFormatError
from ..normalization import normalize_loaded_records


def load_string(
    string: str,
    format: str,
    *,
    normalize: bool = True,
    mapping_fields: frozenset[str] = frozenset(),
    list_fields: frozenset[str] = frozenset(),
    source: str | Path = "<string>",
    header_only: bool = False,
) -> list[dict[str, Any]]:
    """Load records from a string by dispatching to the format-specific loader."""
    try:
        if format == "bib":
            from .bibtex import load_bibtex

            result = load_bibtex(
                string,
                mapping_fields=mapping_fields,
                list_fields=list_fields,
                normalize=normalize,
                header_only=header_only,
            )
        elif format == "ris":
            from .ris import load_ris

            result = load_ris(string, normalize=normalize)
        elif format in {"enl", "nbib", "txt"}:
            from .tagged import load_tagged

            result = load_tagged(string, format=format, normalize=normalize)
        elif format == "csv":
            from .tabular import load_csv

            result = load_csv(string, normalize=normalize)
        elif format == "json":
            from .json import load_json

            result = load_json(string, normalize=normalize)
        elif format == "md":
            from .markdown import load_markdown

            result = load_markdown(string, source=source, normalize=normalize)
        else:
            raise UnsupportedFormatError(f"Reading {format} is unsupported")
        return (
            normalize_loaded_records(result, list_fields=list_fields)
            if normalize
            else result
        )
    except (BackendExecutionError, OptionalBackendUnavailableError, ParseError):
        raise
    except Exception as exc:
        raise ParseError(f"Could not load {format} input: {exc}") from exc
    raise UnsupportedFormatError(f"Reading {format} is unsupported")
