"""Markdown table bibliography writer."""

from __future__ import annotations

from typing import Any

from .table_helpers import table_data


def write_markdown(
    records: dict[str, dict[str, Any]],
    *,
    sort_fields: bool = True,
    sort_by_id: bool = True,
) -> str:
    """Write normalized records as a Markdown table."""
    fields, rows = table_data(records, sort_fields=sort_fields, sort_by_id=sort_by_id)

    def escape(value: Any) -> str:
        return str(value).replace("|", r"\|").replace("\n", " ")

    return (
        "| "
        + " | ".join(fields)
        + " |\n| "
        + " | ".join("---" for _ in fields)
        + " |\n"
        + "\n".join(
            "| " + " | ".join(escape(record.get(key, "")) for key in fields) + " |"
            for record in rows
        )
    )
