"""Excel bibliography writer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..exceptions import OptionalBackendUnavailableError
from .table_helpers import table_data


def write_excel(
    records: dict[str, dict[str, Any]],
    destination: Path,
    *,
    sort_fields: bool = True,
    sort_by_id: bool = True,
) -> None:
    """Write normalized records to Excel with content-sized columns."""
    try:
        import pandas as pd
        from openpyxl.utils import get_column_letter
    except ImportError as exc:
        raise OptionalBackendUnavailableError(
            "Writing Excel files requires Excel dependencies. Install them with "
            "'pip install bibliography-io[excel]'."
        ) from exc

    fields, rows = table_data(records, sort_fields=sort_fields, sort_by_id=sort_by_id)
    dataframe = pd.DataFrame(rows, columns=fields)
    with pd.ExcelWriter(destination, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False)
        worksheet = writer.sheets["Sheet1"]
        for index, field in enumerate(fields, start=1):
            content_width = max((len(str(row[field])) for row in rows), default=0)
            width = max(min(max(content_width, len(field)), 130), 10)
            worksheet.column_dimensions[get_column_letter(index)].width = width
