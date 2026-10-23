"""RIS bibliography loader."""

from __future__ import annotations

import re
from typing import Any

from ..exceptions import ParseError
from ..normalization import _records_from_loaded_list
from ..normalization import _records_from_un_normalized_list
from ..normalization import normalize_field_name

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
            record = {"ENTRYTYPE": RIS_TYPE.get(value.upper(), "misc")}
        elif tag == "ER":
            if record:
                parsed.append(record)
            record = {}
        elif tag == "ID":
            record["ID"] = value
        else:
            key = (
                normalize_field_name(tag, field_aliases=RIS_FIELD_ALIASES)
                if normalize
                else tag
            )
            if key in record:
                record[key] = (
                    [*record[key], value]
                    if isinstance(record[key], list)
                    else [record[key], value]
                )
            else:
                record[key] = value
    if normalize:
        for item in parsed:
            start_page, end_page = (
                item.pop("startpage", None),
                item.pop("endpage", None),
            )
            if start_page is not None:
                item["pages"] = str(start_page) + (f"--{end_page}" if end_page else "")
            if isinstance(item.get("author"), list):
                item["author"] = " and ".join(item["author"])
    if text.strip() and not parsed:
        raise ParseError("No RIS records found")
    if not normalize:
        return _records_from_un_normalized_list(parsed)
    return _records_from_loaded_list(parsed, field_aliases=RIS_FIELD_ALIASES)
