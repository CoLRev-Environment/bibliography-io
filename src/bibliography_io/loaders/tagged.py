"""Tagged-text loaders for EndNote, NBIB, and tagged reference files."""

from __future__ import annotations

import re
from typing import Any

from ..exceptions import ParseError
from ..normalization import _records_from_loaded_list
from ..normalization import normalize_field_name
from ..normalization import normalize_source_record


def load_tagged(text: str, fmt: str) -> list[dict[str, Any]]:
    """Load ENL, NBIB, or TXT records using each format's tag conventions."""
    parsed = []
    current: dict[str, Any] = {}
    lines = text.splitlines() + (["ER  -"] if fmt == "nbib" else [""])
    for line in lines:
        if fmt == "nbib":
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
                elif tag == "PMID":
                    current["pmid"] = value
                elif tag == "PT":
                    current["type"] = normalize_field_name(value)
                else:
                    key = {
                        "TI": "title",
                        "AU": "author",
                        "DP": "year",
                        "JT": "journal",
                        "VI": "volume",
                        "IP": "number",
                        "AB": "abstract",
                        "DO": "doi",
                        "AID": "doi",
                        "PG": "pages",
                    }.get(tag, normalize_field_name(tag))
                    current.setdefault(key, value)
            continue

        match = re.match(r"^%([A-Z0-9])\s+(.*)$", line)
        if match:
            tag, value = match.groups()
            key = {
                "T": "title",
                "A": "author",
                "D": "year",
                "B": "journal",
                "V": "volume",
                "N": "number",
                "P": "pages",
                "U": "url",
                "X": "abstract",
            }.get(tag, normalize_field_name(tag))
            if tag == "0":
                current["type"] = normalize_field_name(value)
            elif tag == "8":
                current["date"] = value
            else:
                current[key] = (
                    f"{current[key]} and {value}"
                    if key == "author" and key in current
                    else value
                )
        elif not line.strip() and current:
            current.setdefault("ENTRYTYPE", "article")
            parsed.append(current)
            current = {}
    if fmt == "nbib" and current:
        current.setdefault("ENTRYTYPE", "article")
        parsed.append(current)
    if text.strip() and not parsed:
        raise ParseError(f"No {fmt.upper()} records found")
    normalized = [normalize_source_record(row, format=fmt) for row in parsed]
    return _records_from_loaded_list(normalized)
