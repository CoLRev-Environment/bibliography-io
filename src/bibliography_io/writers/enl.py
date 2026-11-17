"""EndNote tagged-format bibliography writer."""

from __future__ import annotations

import re
import warnings
from typing import Any

_ENTRYTYPE_MAP = {
    "article": "Journal Article",
    "book": "Book",
    "inbook": "Book Section",
    "incollection": "Book Section",
    "inproceedings": "Inproceedings",
    "mastersthesis": "Thesis",
    "misc": "Generic",
    "phdthesis": "Thesis",
    "proceedings": "Conference Proceedings",
    "techreport": "Report",
    "unpublished": "Manuscript",
}
_FIELD_ORDER = (
    "title",
    "author",
    "year",
    "journal",
    "volume",
    "number",
    "pages",
    "date",
    "url",
    "abstract",
    "doi",
    "keywords",
    "editor",
    "publisher",
    "address",
)
_FIELD_TAGS = {
    "title": "T",
    "author": "A",
    "year": "D",
    "journal": "B",
    "volume": "V",
    "number": "N",
    "pages": "P",
    "date": "8",
    "url": "U",
    "abstract": "X",
    "doi": "R",
    "keywords": "K",
    "editor": "E",
    "publisher": "I",
    "address": "C",
}
_SUPPORTED_FIELDS = {"ID", "ENTRYTYPE", *_FIELD_TAGS}
_PLACEHOLDERS = {"", "None", "UNKNOWN", "nan"}


def _values(field: str, value: Any) -> list[str]:
    """Convert a field value to its non-empty tagged values."""
    values = value if isinstance(value, (list, tuple, set)) else [value]
    if isinstance(values, set):
        values = sorted(values)

    output = []
    for item in values:
        if item is None:
            continue
        text = " ".join(str(item).splitlines()).strip()
        if text in _PLACEHOLDERS:
            continue
        if field == "author":
            output.extend(
                author.strip()
                for author in re.split(r"\s+and\s+", text)
                if author.strip()
            )
        elif field == "keywords":
            output.extend(
                keyword.strip() for keyword in text.split(";") if keyword.strip()
            )
        else:
            output.append(text)
    return output


def write_enl(records: dict[str, dict[str, Any]]) -> str:
    """Write normalized records as EndNote tagged text."""
    entries = []
    for record_id, record in records.items():
        for field in record:
            if field not in _SUPPORTED_FIELDS:
                warnings.warn(
                    f"Skipping unsupported ENL field {field!r} in record {record_id!r}",
                    UserWarning,
                    stacklevel=2,
                )

        entrytype = str(record.get("ENTRYTYPE", "misc")).lower()
        lines = [f"%0 {_ENTRYTYPE_MAP.get(entrytype, 'Generic')}"]
        for field in _FIELD_ORDER:
            tag = _FIELD_TAGS[field]
            lines.extend(
                f"%{tag} {value}" for value in _values(field, record.get(field, ""))
            )
        entries.append("\n".join(lines))
    return "\n\n".join(entries)
