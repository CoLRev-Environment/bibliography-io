"""CSV and Excel bibliography loaders."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from typing import Any

from ..exceptions import OptionalBackendUnavailableError
from ..exceptions import ParseError
from ..normalization import _records_from_loaded_list
from ..normalization import _records_from_un_normalized_list
from ..normalization import normalize_source_rows

TABULAR_FIELD_ALIASES = {
    "authors": "author",
    "issue": "number",
    "journalbook": "journal_book",
    "publication_year": "year",
    "publicationyear": "year",
}


def load_csv(text: str, *, normalize: bool = True) -> list[dict[str, Any]]:
    """Load CSV rows as bibliography records."""
    rows = list(csv.DictReader(StringIO(text)))
    if not normalize:
        return _records_from_un_normalized_list(rows)
    return _records_from_loaded_list(
        normalize_source_rows(rows, field_aliases=TABULAR_FIELD_ALIASES)
    )


def load_excel(
    source: Path, format: str, *, normalize: bool = True
) -> list[dict[str, Any]]:
    """Load Excel rows as bibliography records using the optional Excel extra."""
    try:
        import pandas as pd

        rows = pd.read_excel(source).fillna("").to_dict(orient="records")
        if not normalize:
            return _records_from_un_normalized_list(rows)
        normalized = normalize_source_rows(
            rows, field_aliases=TABULAR_FIELD_ALIASES, format=format
        )
        return _records_from_loaded_list(normalized)
    except ImportError as exc:
        raise OptionalBackendUnavailableError(
            f"Reading {format} files requires Excel dependencies. Install them with "
            "'pip install bibliography-io[excel]'."
        ) from exc
    except OptionalBackendUnavailableError:
        raise
    except Exception as exc:
        raise ParseError(f"Could not parse {format} file {source}: {exc}") from exc
