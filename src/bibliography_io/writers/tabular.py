"""CSV and Markdown table writers."""

from __future__ import annotations

import csv
from io import StringIO
from typing import Any


def serialize_table(records: dict[str, dict[str, Any]], fmt: str) -> str:
    """Serialize normalized records as CSV or a Markdown table."""
    fields = list(dict.fromkeys(key for record in records.values() for key in record))
    if fmt == "csv":
        stream = StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(records.values())
        return stream.getvalue()

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
            for record in records.values()
        )
    )
