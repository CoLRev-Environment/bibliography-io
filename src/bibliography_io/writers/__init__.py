"""Format-specific bibliography writers."""

from __future__ import annotations

from typing import Any

from ..exceptions import UnsupportedFormatError
from ..normalization import normalize_format
from ..normalization import normalize_records
from ..normalization import sort_records_by_id

WRITE_FORMATS = {"bib", "ris", "csv", "xlsx", "md"}


def write_string(
    records: Any,
    format: str,
    *,
    mapping_fields: frozenset[str] = frozenset(),
    list_fields: frozenset[str] = frozenset(),
    field_order: tuple[str, ...] | None = None,
    sort_fields: bool = True,
    sort_by_id: bool = True,
) -> str:
    """Normalize records and dispatch writing to a format-specific writer."""
    if not isinstance(sort_fields, bool):
        raise TypeError("sort_fields must be a bool")
    if not isinstance(sort_by_id, bool):
        raise TypeError("sort_by_id must be a bool")
    format_name = normalize_format(format)
    if format_name not in WRITE_FORMATS:
        raise UnsupportedFormatError(f"Writing {format_name} is unsupported")
    data = normalize_records(records, format="bib" if format_name == "bib" else None)
    if sort_by_id:
        data = sort_records_by_id(data)
    if format_name == "bib":
        from .bibtex import write_bibtex

        return write_bibtex(
            data,
            mapping_fields=mapping_fields,
            list_fields=list_fields,
            field_order=field_order,
            sort_fields=sort_fields,
        )
    if format_name == "ris":
        from .ris import write_ris

        return write_ris(data)
    if format_name in {"csv", "md"}:
        from .tabular import write_table

        return write_table(data, format=format_name)
    raise UnsupportedFormatError(f"Writing {format_name} is unsupported")
