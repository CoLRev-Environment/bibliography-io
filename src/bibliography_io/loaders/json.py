"""JSON bibliography loader."""

from __future__ import annotations

import json
from typing import Any

from ..normalization import _records_from_list


def load_json(text: str) -> list[dict[str, Any]]:
    """Load a JSON list of records."""
    return _records_from_list(json.loads(text))
