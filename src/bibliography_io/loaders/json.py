"""JSON bibliography loader."""

from __future__ import annotations

import json
from typing import Any

from ..normalization import _records_from_un_normalized_list
from ..normalization import normalize_source_record

JSON_FIELD_ALIASES = {"authors": "author"}


def normalize_without_source(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply JSON field aliases before shared record validation."""
    return [
        normalize_source_record(
            record,
            field_aliases=JSON_FIELD_ALIASES,
            generic_normalization=True,
        )
        for record in _records_from_un_normalized_list(records)
    ]


def load_json(
    text: str, *, normalize: bool = True
) -> list[dict[str, Any]] | dict[str, dict[str, Any]]:
    """Load a JSON list of records."""
    records = json.loads(text)
    if normalize:
        from .. import _normalize_without_source

        return _normalize_without_source(records, format_name="json")
    return _records_from_un_normalized_list(records)
