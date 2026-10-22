"""BibTeX bibliography writer."""

from __future__ import annotations

import base64
import json
from typing import Any

from ..exceptions import SerializationError

_STRUCTURED_BIB_PREFIX = "bibio-json-v1:"


def _escape(value: Any) -> str:
    if isinstance(value, (dict, list, tuple, set)):
        raise SerializationError(f"Cannot serialize non-scalar BibTeX value: {value!r}")
    return "{" + str(value).replace("}", r"\}") + "}"


def _encode_structured(value: Any, field: str) -> str:
    try:
        payload = json.dumps(
            value, ensure_ascii=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise SerializationError(
            f"Cannot serialize structured BibTeX field {field!r}: {exc}"
        ) from exc
    return _STRUCTURED_BIB_PREFIX + base64.b64encode(payload).decode("ascii")


def serialize_bibtex(
    records: dict[str, dict[str, Any]],
    *,
    mapping_fields: frozenset[str] = frozenset(),
    list_fields: frozenset[str] = frozenset(),
) -> str:
    """Serialize normalized records to BibTeX."""
    entries = []
    for record in records.values():
        fields = []
        field_width = max(
            (len(key) for key in record if key not in {"ID", "ENTRYTYPE"}),
            default=0,
        )
        for key, value in record.items():
            if key in {"ID", "ENTRYTYPE"}:
                continue
            field_name = key.lower()
            if field_name in mapping_fields | list_fields:
                expected_type = dict if field_name in mapping_fields else list
                expected_label = "mapping" if expected_type is dict else "list"
                if not isinstance(value, expected_type):
                    raise SerializationError(
                        f"BibTeX field {key!r} was declared as a {expected_label} "
                        f"field but has value {value!r}"
                    )
                value = "{" + _encode_structured(value, key) + "}"
            else:
                value = _escape(value)
            fields.append(f"  {key:<{field_width}} = {value}")
        entries.append(
            f"@{record['ENTRYTYPE']}{{{record['ID']},\n" + ",\n".join(fields) + "\n}"
        )
    return "\n\n".join(entries)
