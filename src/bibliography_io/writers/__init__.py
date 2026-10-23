"""Format-specific bibliography writers."""

from __future__ import annotations

from typing import Any

from ..exceptions import UnsupportedFormatError
from ..normalization import normalize_format
from ..normalization import normalize_records

WRITE_FORMATS = {"bib", "ris", "csv", "xlsx", "md"}


def write_string(
    records: Any,
    format: str,
    *,
    mapping_fields: frozenset[str] = frozenset(),
    list_fields: frozenset[str] = frozenset(),
    field_order: tuple[str, ...] | None = None,
) -> str:
    """Normalize records and dispatch writing to a format-specific writer."""
    format_name = normalize_format(format)
    if format_name not in WRITE_FORMATS:
        raise UnsupportedFormatError(f"Writing {format_name} is unsupported")
    data = normalize_records(records, format="bib" if format_name == "bib" else None)
    if format_name == "bib":
        from .bibtex import write_bibtex

        return write_bibtex(
            data,
            mapping_fields=mapping_fields,
            list_fields=list_fields,
            field_order=field_order,
        )
    if format_name == "ris":
        from .ris import write_ris

        return write_ris(data)
    if format_name in {"csv", "md"}:
        from .tabular import write_table

        return write_table(data, format=format_name)
    raise UnsupportedFormatError(f"Writing {format_name} is unsupported")
