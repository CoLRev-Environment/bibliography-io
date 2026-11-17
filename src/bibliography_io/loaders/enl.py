"""EndNote tagged-format loader."""

from __future__ import annotations

import re
from typing import Any

from ..exceptions import ParseError
from ..normalization import _records_from_un_normalized_list

_ENL_FIELD_MAP = {
    "T": "title",
    "A": "author",
    "C": "address",
    "D": "year",
    "B": "journal",
    "E": "editor",
    "I": "publisher",
    "K": "keywords",
    "V": "volume",
    "N": "number",
    "P": "pages",
    "R": "doi",
    "X": "abstract",
    "U": "url",
    "8": "date",
}
_ENL_ENTRYTYPE_MAP = {
    "Journal Article": "article",
    "Book": "book",
    "Book Section": "incollection",
    "Inproceedings": "inproceedings",
    "Thesis": "phdthesis",
    "Conference Proceedings": "proceedings",
    "Report": "techreport",
    "Manuscript": "unpublished",
    "Generic": "misc",
}


def normalize_without_source(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map EndNote tags and reference types to bibliography fields."""
    for index, record in enumerate(records, start=1):
        raw_type = record.pop("0", None)
        if raw_type is not None:
            record["ENTRYTYPE"] = _ENL_ENTRYTYPE_MAP.get(raw_type, "misc")
        else:
            record["ENTRYTYPE"] = (
                "article" if "V" in record or "N" in record else "inproceedings"
            )
        for source, target in _ENL_FIELD_MAP.items():
            if source in record:
                record[target] = record.pop(source)
        record.pop("type", None)
        record.setdefault("ID", str(index))
    return records


def load_enl(
    text: str, *, normalize: bool = True
) -> list[dict[str, Any]] | dict[str, dict[str, Any]]:
    """Load EndNote tagged records, optionally normalizing their field codes."""
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
        raise ParseError("No ENL records found")
    if normalize:
        from .. import _normalize_without_source

        return _normalize_without_source(parsed, format_name="enl")
    return _records_from_un_normalized_list(parsed)
