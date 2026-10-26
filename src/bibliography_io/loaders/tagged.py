"""Tagged-text loaders for EndNote, NBIB, and tagged reference files."""

from __future__ import annotations

import re
from typing import Any

from ..exceptions import ParseError
from ..normalization import _records_from_loaded_list
from ..normalization import _records_from_un_normalized_list
from ..normalization import normalize_field_name
from ..normalization import normalize_source_record


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
                elif tag == "PMID":
                    current["pmid" if normalize else tag] = value
                elif tag == "PT":
                    key = "type" if normalize else "PT"
                    parsed_value = normalize_field_name(value) if normalize else value
                    if key not in current:
                        current[key] = parsed_value
                    elif isinstance(current[key], list):
                        current[key].append(parsed_value)
                    else:
                        current[key] = [current[key], parsed_value]
                else:
                    key = (
                        {
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
                            "OT": "keywords",
                        }.get(tag, normalize_field_name(tag))
                        if normalize
                        else tag
                    )
                    if key == "author" and key in current:
                        current[key] = f"{current[key]} and {value}"
                    elif key in current:
                        previous = current[key]
                        current[key] = (
                            [*previous, value]
                            if isinstance(previous, list)
                            else [previous, value]
                        )
                    else:
                        current[key] = value
            continue

        match = re.match(r"^%([A-Z0-9])\s+(.*)$", line)
        if match:
            tag, value = match.groups()
            key = (
                {
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
                if normalize
                else tag
            )
            if tag == "0":
                current["type" if normalize else tag] = (
                    normalize_field_name(value) if normalize else value
                )
            elif tag == "8":
                current["date" if normalize else tag] = value
            else:
                if key == "author" and key in current:
                    current[key] = f"{current[key]} and {value}"
                elif not normalize and key in current:
                    previous = current[key]
                    current[key] = (
                        [*previous, value]
                        if isinstance(previous, list)
                        else [previous, value]
                    )
                else:
                    current[key] = value
        elif not line.strip() and current:
            current.setdefault("ENTRYTYPE", "article")
            parsed.append(current)
            current = {}
    if format == "nbib" and current:
        current.setdefault("ENTRYTYPE", "article")
        parsed.append(current)
    if text.strip() and not parsed:
        raise ParseError(f"No {format.upper()} records found")
    if not normalize:
        return _records_from_un_normalized_list(parsed)
    normalized = [normalize_source_record(row, format=format) for row in parsed]
    return _records_from_loaded_list(normalized)
