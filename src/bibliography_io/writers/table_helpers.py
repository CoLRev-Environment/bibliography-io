"""Shared layout helpers for tabular bibliography writers."""

from __future__ import annotations

import math
from typing import Any

_PREFERRED_FIELDS = (
    "ID",
    "ENTRYTYPE",
    "title",
    "author",
    "year",
    "journal",
    "booktitle",
    "volume",
    "number",
    "pages",
    "doi",
    "url",
    "file",
)


def table_data(
    records: dict[str, dict[str, Any]],
    *,
    sort_fields: bool = True,
    sort_by_id: bool = True,
) -> tuple[list[str], list[dict[str, Any]]]:
    """Return ordered records and fields, dropping columns without values."""
    all_fields = list(
        dict.fromkeys(field for record in records.values() for field in record)
    )
    if sort_fields:
        available_fields = set(all_fields)
        additional_fields = sorted(available_fields - set(_PREFERRED_FIELDS))
        fields = [field for field in _PREFERRED_FIELDS if field in available_fields]
        fields.extend(additional_fields)
    else:
        fields = all_fields

    sorted_records = list(records.items())
    if sort_by_id:
        sorted_records.sort(key=lambda item: str(item[1].get("ID", item[0])))
    rows = [
        {field: record.get(field, "") for field in fields}
        for _, record in sorted_records
    ]
    fields = [
        field for field in fields if any(not _is_empty(row[field]) for row in rows)
    ]
    rows = [{field: row[field] for field in fields} for row in rows]
    return fields, rows


def _is_empty(value: Any) -> bool:
    if value is None or (isinstance(value, str) and value == ""):
        return True
    try:
        return math.isnan(value)
    except (TypeError, ValueError):
        return False
