"""Tagged-text loaders for EndNote, NBIB, and tagged reference files."""

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
_ENL_FIELD_MAP = {
    "T": "title",
    "A": "author",
    "D": "year",
    "B": "journal",
    "V": "volume",
    "N": "number",
    "P": "pages",
    "X": "abstract",
    "U": "url",
    "8": "date",
}


def _append_normalized_value(record: dict[str, Any], key: str, value: Any) -> None:
    """Append values mapped from multiple source tags without losing repeats."""
    if key not in record:
        record[key] = value
        return
    previous = record[key]
    values = previous if isinstance(previous, list) else [previous]
    new_values = value if isinstance(value, list) else [value]
    record[key] = [*values, *new_values]


def normalize_without_source(
    records: list[dict[str, Any]], *, format: str
) -> list[dict[str, Any]]:
    """Map tagged records using the selected format's no-source conventions."""
    if format == "nbib":
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
    elif format == "enl":
        for index, record in enumerate(records, start=1):
            raw_type = record.pop("0", None)
            if raw_type is not None:
                record["ENTRYTYPE"] = {
                    "Journal Article": "article",
                    "Inproceedings": "inproceedings",
                }.get(raw_type, "misc")
            else:
                record["ENTRYTYPE"] = (
                    "article" if "V" in record or "N" in record else "inproceedings"
                )
            for source, target in _ENL_FIELD_MAP.items():
                if source in record:
                    record[target] = record.pop(source)
            record.pop("type", None)
            record.setdefault("ID", str(index))
    elif format == "txt":
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
    else:
        raise ValueError(f"Unsupported tagged format: {format}")
    return records


def load_tagged(
    text: str, format: str, *, normalize: bool = True
) -> list[dict[str, Any]]:
    """Load ENL, NBIB, or TXT records using each format's tag conventions."""
    parsed = []
    current: dict[str, Any] = {}
    lines = text.splitlines() + (["ER  -"] if format == "nbib" else [""])
    for line in lines:
        if format == "nbib":
            match = re.match(r"^([A-Z0-9]{2,4})\s+-\s+(.*)$", line)
            if not line.strip() and current:
                current.setdefault("ENTRYTYPE", "article")
                parsed.append(current)
                current = {}
                continue
            if not line.strip():
                continue
            if match:
                tag, value = match.groups()
                if tag == "ER":
                    if current:
                        current.setdefault("ENTRYTYPE", "article")
                        parsed.append(current)
                        current = {}
                else:
                    if tag in current:
                        previous = current[tag]
                        current[tag] = (
                            [*previous, value]
                            if isinstance(previous, list)
                            else [previous, value]
                        )
                    else:
                        current[tag] = value
            continue

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
    if format == "nbib" and current:
        current.setdefault("ENTRYTYPE", "article")
        parsed.append(current)
    if text.strip() and not parsed:
        raise ParseError(f"No {format.upper()} records found")
    if normalize:
        from .. import _normalize_without_source

        return _normalize_without_source(parsed, format_name=format)
    return _records_from_un_normalized_list(parsed)
