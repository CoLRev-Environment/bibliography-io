"""RIS bibliography loader."""

from __future__ import annotations

import re
from typing import Any

from ..exceptions import ParseError
from ..normalization import _records_from_un_normalized_list

RIS_MAP = {
    "TI": "title",
    "T1": "title",
    "AU": "author",
    "A1": "author",
    "PY": "year",
    "Y1": "year",
    "DA": "year",
    "JO": "journal",
    "JF": "journal",
    "T2": "journal",
    "BT": "booktitle",
    "VL": "volume",
    "IS": "number",
    "SP": "startpage",
    "EP": "endpage",
    "DO": "doi",
    "UR": "url",
    "AB": "abstract",
    "PB": "publisher",
    "SN": "issn",
    "KW": "keywords",
    "PMID": "pubmed_id",
}
RIS_FIELD_ALIASES = {tag.lower(): field for tag, field in RIS_MAP.items()}
RIS_FIELD_ALIASES.update({"vo": "volume", "ja": "journal_abbreviation"})
RIS_TYPE = {
    "JOUR": "article",
    "CONF": "inproceedings",
    "CPAPER": "inproceedings",
    "BOOK": "book",
    "CHAP": "inbook",
    "THES": "phdthesis",
    "RPRT": "techreport",
}
_RIS_NO_SOURCE_TYPES = {
    **RIS_TYPE,
    "JFULL": "article",
    "ABST": "article",
    "INPR": "article",
    "NEWS": "misc",
    "BLOG": "misc",
}


def normalize_without_source(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map recognized RIS tags while preserving unknown tags."""
    field_map = {
        "TI": "title",
        "T1": "title",
        "PY": "year",
        "Y1": "year",
        "DA": "year",
        "AU": "author",
        "A1": "author",
        "JO": "journal",
        "JF": "journal",
        "JA": "journal",
        "DO": "doi",
        "VL": "volume",
        "IS": "number",
        "UR": "url",
        "SN": "issn",
        "AB": "abstract",
        "KW": "keywords",
        "PB": "publisher",
    }
    for index, record in enumerate(records, start=1):
        raw_type = str(record.pop("TY", "")).strip().upper()
        record.setdefault("ENTRYTYPE", _RIS_NO_SOURCE_TYPES.get(raw_type, "misc"))
        for tag, target in field_map.items():
            if target not in record and tag in record:
                record[target] = record[tag]
            if target in record:
                record.pop(tag, None)
        container_field = (
            "booktitle" if record.get("ENTRYTYPE") == "inproceedings" else "journal"
        )
        container_tags = (
            ("T2",) if container_field == "booktitle" else ("JO", "JF", "JA", "T2")
        )
        if container_field not in record:
            for tag in container_tags:
                if tag in record and str(record[tag]).strip():
                    record[container_field] = record[tag]
                    break
        if container_field in record:
            for tag in container_tags:
                record.pop(tag, None)
        year = record.get("year")
        if year is not None:
            year_match = re.search(r"(?<!\d)(\d{4})(?!\d)", str(year))
            if year_match:
                record["year"] = year_match.group(1)
        if isinstance(record.get("keywords"), list):
            record["keywords"] = ", ".join(record["keywords"])
        if "pages" not in record and "SP" in record:
            record["pages"] = str(record.pop("SP")) + (
                f"--{record.pop('EP')}" if "EP" in record else ""
            )
        if "pages" in record:
            record.pop("SP", None)
            record.pop("EP", None)
        for source, target in (("fulltext", "fulltext"), ("PMID", "pubmed_id")):
            if source in record and target not in record:
                record[target] = record.pop(source)
        for key in ("C1", "T3", "AD", "CY", "M3", "ER", "Y2", "DB"):
            record.pop(key, None)
        record["ID"] = str(index).zfill(6)
    return records


def load_ris(text: str, *, normalize: bool = True) -> list[dict[str, Any]]:
    """Load RIS records, optionally mapping tags to bibliography fields."""
    parsed = []
    record: dict[str, Any] = {}
    for line in text.splitlines() + ["ER  - "]:
        match = re.match(r"^\s*([A-Z0-9]{2,4})\s+-\s?(.*)$", line)
        if not match:
            continue
        tag, value = match.groups()
        if tag == "TY":
            if record:
                parsed.append(record)
            record = {"TY": value}
        elif tag == "ER":
            if record:
                parsed.append(record)
            record = {}
        elif tag == "ID":
            record["ID"] = value
        else:
            key = tag
            if key in record:
                record[key] = (
                    [*record[key], value]
                    if isinstance(record[key], list)
                    else [record[key], value]
                )
            else:
                record[key] = value
    if text.strip() and not parsed:
        raise ParseError("No RIS records found")
    if normalize:
        from .. import _normalize_without_source

        return _normalize_without_source(parsed, format_name="ris")
    return _records_from_un_normalized_list(parsed)
