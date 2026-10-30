"""JSON bibliography loader."""

from __future__ import annotations

import json
from typing import Any

from ..normalization import _records_from_list
from ..normalization import _records_from_un_normalized_list

JSON_FIELD_ALIASES = {"authors": "author"}


def load_json(text: str, *, normalize: bool = True) -> list[dict[str, Any]]:
    """Load a JSON list of records."""
    records = json.loads(text)
    return (
        _records_from_list(records, field_aliases=JSON_FIELD_ALIASES)
        if normalize
        else _records_from_un_normalized_list(records)
    )
