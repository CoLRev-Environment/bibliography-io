"""EndNote TXT tagged bibliography loader."""

from __future__ import annotations

import re
from typing import Any

from ..exceptions import ParseError
from ..normalization import _records_from_un_normalized_list
from ..normalization import normalize_field_name

_TXT_FIELD_MAP = {
    "T": "title",
    "A": "author",
    "D": "year",
    "B": "journal",
    "V": "volume",
    "N": "number",
    "P": "pages",
    "U": "url",
    "X": "abstract",
}


def _append_normalized_value(record: dict[str, Any], key: str, value: Any) -> None:
    """Append repeated values while normalizing TXT records."""
    if key not in record:
        record[key] = value
        return
    previous = record[key]
    values = previous if isinstance(previous, list) else [previous]
    new_values = value if isinstance(value, list) else [value]
    record[key] = [*values, *new_values]


def normalize_without_source(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map EndNote TXT tags without applying ENL reference-type mappings."""
    for record in records:
        for tag in list(record):
            if tag == "ENTRYTYPE":
                continue
            value = record.pop(tag)
            if tag == "0":
                record["type"] = normalize_field_name(str(value))
            elif tag == "8":
                record["date"] = value
            else:
                target = _TXT_FIELD_MAP.get(tag, tag)
                _append_normalized_value(record, target, value)
    return records


def load_txt(
    text: str, *, normalize: bool = True
) -> list[dict[str, Any]] | dict[str, dict[str, Any]]:
    """Load EndNote TXT records using its percent-tag syntax."""
    parsed = []
    current: dict[str, Any] = {}
    for line in text.splitlines() + [""]:
        match = re.match(r"^%([A-Z0-9])\s+(.*)$", line)
        if match:
            tag, value = match.groups()
            if tag in current:
                previous = current[tag]
                current[tag] = (
                    [*previous, value]
                    if isinstance(previous, list)
                    else [previous, value]
                )
            else:
                current[tag] = value
        elif not line.strip() and current:
            current.setdefault("ENTRYTYPE", "article")
            parsed.append(current)
            current = {}
    if text.strip() and not parsed:
        raise ParseError("No TXT records found")
    if normalize:
        from .. import _normalize_without_source

        return _normalize_without_source(parsed, format_name="txt")
    return _records_from_un_normalized_list(parsed)
