"""Format-specific bibliography writers."""

from __future__ import annotations

from typing import Any

from ..exceptions import UnsupportedFormatError
from ..normalization import normalize_format
from ..normalization import normalize_records

WRITE_FORMATS = {"bib", "ris", "csv", "xlsx", "md"}


def serialize(
    records: Any,
    format: str,
    *,
    mapping_fields: frozenset[str] = frozenset(),
    list_fields: frozenset[str] = frozenset(),
) -> str:
    """Normalize records and dispatch serialization to a format writer."""
    fmt = normalize_format(format)
    if fmt not in WRITE_FORMATS:
        raise UnsupportedFormatError(f"Writing {fmt} is unsupported")
    data = normalize_records(records)
    if fmt == "bib":
        from .bibtex import serialize_bibtex

        return serialize_bibtex(
            data, mapping_fields=mapping_fields, list_fields=list_fields
        )
    if fmt == "ris":
        from .ris import serialize_ris

        return serialize_ris(data)
    if fmt in {"csv", "md"}:
        from .tabular import serialize_table

        return serialize_table(data, fmt)
    raise UnsupportedFormatError(f"Writing {fmt} is unsupported")
