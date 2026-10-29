"""RIS bibliography writer."""

from __future__ import annotations

import warnings
from typing import Any

_ENTRYTYPE_MAP = {
    "article": "JOUR",
    "book": "BOOK",
    "inproceedings": "CONF",
    "proceedings": "CONF",
    "incollection": "CONF",
    "misc": "GEN",
    "phdthesis": "THES",
    "techreport": "RPRT",
    "unpublished": "UNPB",
}

_RECORD_FIELD_MAP = {
    "TI": "title",
    "PY": "year",
    "JO": "journal",
    "VL": "volume",
    "IS": "number",
    "N2": "abstract",
    "UR": "url",
    "DO": "doi",
}
_FIELD_ORDER = (
    "TI",
    "AU",
    "PY",
    "SP",
    "EP",
    "JO",
    "VL",
    "IS",
    "N2",
    "UR",
    "SN",
    "DO",
)
_SUPPORTED_FIELDS = {
    "ID",
    "ENTRYTYPE",
    "title",
    "author",
    "year",
    "pages",
    "journal",
    "volume",
    "number",
    "abstract",
    "url",
    "doi",
    "issn",
    "isbn",
}
_PLACEHOLDERS = {"", "None", "UNKNOWN", "nan"}


def _is_present(value: Any) -> bool:
    return str(value) not in _PLACEHOLDERS


def _page_values(record: dict[str, Any]) -> list[tuple[str, str]]:
    if "pages" not in record or not _is_present(record["pages"]):
        return []
    pages = str(record["pages"])
    separator = "--" if "--" in pages else "-" if pages.count("-") == 1 else None
    if separator is None:
        return [("SP", pages)]
    start, end = pages.split(separator, 1)
    return [("SP", start), ("EP", end)]


def write_ris(records: dict[str, dict[str, Any]]) -> str:
    """Write normalized records as RIS using the legacy field set and order."""
    lines = []
    for record_id in sorted(records):
        record = records[record_id]
        for field in record:
            if field not in _SUPPORTED_FIELDS:
                warnings.warn(
                    f"Skipping unsupported RIS field {field!r} in record {record_id!r}",
                    UserWarning,
                    stacklevel=2,
                )

        entrytype = record.get("ENTRYTYPE", "misc")
        lines.append(f"TY  - {_ENTRYTYPE_MAP.get(entrytype, 'GEN')}")
        for tag in _FIELD_ORDER:
            if tag == "AU":
                authors = str(record.get("author", "")).strip()
                if _is_present(authors):
                    lines.extend(
                        f"AU  - {author.strip()}" for author in authors.split(" and ")
                    )
            elif tag in _RECORD_FIELD_MAP:
                value = record.get(_RECORD_FIELD_MAP[tag], "")
                if _is_present(value):
                    lines.append(f"{tag}  - {value}")
            elif tag == "SP":
                lines.extend(
                    f"{page_tag}  - {value}" for page_tag, value in _page_values(record)
                )
            elif tag == "SN":
                for field in ("issn", "isbn"):
                    value = record.get(field, "")
                    if _is_present(value):
                        lines.append(f"SN  - {value}")

        lines.extend([f"ID  - {record.get('ID', record_id)}", "ER  -", ""])
    return "\n".join(lines).rstrip()
