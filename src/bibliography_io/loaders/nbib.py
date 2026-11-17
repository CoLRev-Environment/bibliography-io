"""PubMed NBIB bibliography loader."""

from __future__ import annotations

import re
from typing import Any

from ..exceptions import ParseError
from ..normalization import _records_from_un_normalized_list
from ..normalization import normalize_field_name

_NBIB_FIELD_MAP = {
    "TI": "title",
    "AU": "author",
    "OWN": "own",
    "DP": "year",
    "JT": "journal",
    "SO": "so",
    "OID": "oid",
    "LID": "lid",
    "LA": "la",
    "VI": "volume",
    "IP": "number",
    "AB": "abstract",
    "DO": "doi",
    "AID": "doi",
    "PG": "pages",
    "OT": "keywords",
}


def _append_normalized_value(record: dict[str, Any], key: str, value: Any) -> None:
    """Append repeated values while normalizing NBIB records."""
    if key not in record:
        record[key] = value
        return
    previous = record[key]
    values = previous if isinstance(previous, list) else [previous]
    new_values = value if isinstance(value, list) else [value]
    record[key] = [*values, *new_values]


def normalize_without_source(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map PubMed tags while preserving unrecognized tags."""
    for record in records:
        for tag in list(record):
            value = record.pop(tag)
            if tag == "ENTRYTYPE":
                record[tag] = value
                continue
            if tag == "PMID":
                target = "pmid"
            elif tag == "PT":
                target = "type"
                value = (
                    [normalize_field_name(str(item)) for item in value]
                    if isinstance(value, list)
                    else normalize_field_name(str(value))
                )
            else:
                target = _NBIB_FIELD_MAP.get(tag, tag)
            _append_normalized_value(record, target, value)
    return records


def load_nbib(
    text: str, *, normalize: bool = True
) -> list[dict[str, Any]] | dict[str, dict[str, Any]]:
    """Load NBIB records using PubMed's tag and record-boundary syntax."""
    parsed = []
    current: dict[str, Any] = {}
    for line in text.splitlines() + ["ER  -"]:
        match = re.match(r"^([A-Z0-9]{2,4})\s+-\s+(.*)$", line)
        if not line.strip():
            if current:
                current.setdefault("ENTRYTYPE", "article")
                parsed.append(current)
                current = {}
            continue
        if not match:
            continue
        tag, value = match.groups()
        if tag == "ER":
            if current:
                current.setdefault("ENTRYTYPE", "article")
                parsed.append(current)
                current = {}
        elif tag in current:
            previous = current[tag]
            current[tag] = (
                [*previous, value]
                if isinstance(previous, list)
                else [previous, value]
            )
        else:
            current[tag] = value
    if current:
        current.setdefault("ENTRYTYPE", "article")
        parsed.append(current)
    if text.strip() and not parsed:
        raise ParseError("No NBIB records found")
    if normalize:
        from .. import _normalize_without_source

        return _normalize_without_source(parsed, format_name="nbib")
    return _records_from_un_normalized_list(parsed)
