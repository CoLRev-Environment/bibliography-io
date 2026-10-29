"""CSV bibliography writer."""

from __future__ import annotations

import csv
from io import StringIO
from typing import Any

from .table_helpers import table_data


def write_csv(
    records: dict[str, dict[str, Any]],
    *,
    sort_fields: bool = True,
    sort_by_id: bool = True,
) -> str:
    """Write normalized records as CSV."""
    fields, rows = table_data(records, sort_fields=sort_fields, sort_by_id=sort_by_id)
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()
