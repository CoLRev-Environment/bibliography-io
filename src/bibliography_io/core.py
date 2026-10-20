"""Standalone parsing and serialization used by the strict public API."""

from __future__ import annotations

import csv
import base64
import json
import re
from collections import OrderedDict
from io import StringIO
from typing import Any

from .exceptions import DuplicateRecordIDError
from .exceptions import OptionalBackendUnavailableError
from .exceptions import ParseError
from .exceptions import RecordValidationError
from .exceptions import SerializationError
from .exceptions import UnsupportedFormatError

READ_FORMATS = {"bib", "ris", "csv", "xls", "xlsx", "enl", "txt", "nbib", "json", "md"}
WRITE_FORMATS = {"bib", "ris", "csv", "xlsx", "md"}
ALIASES = {"bibtex": "bib", "markdown": "md", "excel": "xlsx", "endnote": "enl"}

FIELD_ALIASES = {
    "title": "title",
    "ti": "title",
    "t1": "title",
    "authors": "author",
    "author": "author",
    "au": "author",
    "a1": "author",
    "publication_year": "year",
    "publicationyear": "year",
    "year": "year",
    "py": "year",
    "dp": "year",
    "y1": "year",
    "doi": "doi",
    "do": "doi",
    "aid": "doi",
    "journal": "journal",
    "journal_book": "journal_book",
    "journalbook": "journal_book",
    "container_title": "container_title",
    "jo": "journal",
    "jf": "journal",
    "ja": "journal_abbreviation",
    "t2": "journal",
    "booktitle": "booktitle",
    "bt": "booktitle",
    "volume": "volume",
    "vl": "volume",
    "vi": "volume",
    "vo": "volume",
    "number": "number",
    "issue": "number",
    "is": "number",
    "ip": "number",
    "pages": "pages",
    "pg": "pages",
    "url": "url",
    "ur": "url",
    "issn": "issn",
    "sn": "issn",
    "abstract": "abstract",
    "ab": "abstract",
    "keywords": "keywords",
    "kw": "keywords",
    "pmid": "pmid",
    "pubmed_id": "pubmed_id",
    "pmcid": "pmcid",
    "nihms_id": "nihms_id",
    "first_author": "first_author",
    "citation": "citation",
    "journal_abbreviation": "journal_abbreviation",
    "create_date": "create_date",
    "date": "date",
    "number_of_cited_references": "number_of_cited_references",
    "file_name": "file_name",
    "author_count": "author_count",
    "citation_key": "citation_key",
    "cited_by": "cited_by",
    "source_type": "source_type",
    "type": "type",
    "id": "id",
    "entrytype": "ENTRYTYPE",
}

_TABLE_FORMATS = {"csv", "xlsx", "xls"}
_STRUCTURED_BIB_PREFIX = "bibio-json-v1:"


def normalize_field_name(value: str) -> str:
    """Normalize arbitrary source field labels to bibliography-io field names."""
    name = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    name = re.sub(r"_+", "_", name)
    return FIELD_ALIASES.get(name, name)


def normalize_source_record(
    record: dict[str, Any], *, format: str | None = None
) -> dict[str, Any]:
    """Normalize source field names and combine aliases without losing values."""
    normalized: dict[str, Any] = {}
    raw_entrytype = record.get("ENTRYTYPE")
    for field, value in record.items():
        if field in {"ID", "ENTRYTYPE"}:
            normalized[field] = value
            continue
        if str(field).lower() == "entrytype":
            normalized["ENTRYTYPE"] = value
            continue
        key = normalize_field_name(str(field))
        if key == "id" and format in _TABLE_FORMATS:
            normalized[key] = value
            continue
        if key == "journal_book":
            if format in _TABLE_FORMATS:
                if record.get("journal"):
                    key = "container_title"
                elif record.get("booktitle"):
                    key = "booktitle"
                elif value:
                    key = "journal"
                else:
                    key = "booktitle"
            elif raw_entrytype == "inproceedings" or record.get("booktitle"):
                key = "booktitle"
            elif raw_entrytype == "article":
                key = "journal"
            else:
                key = "booktitle"
        if key not in normalized or normalized[key] in (None, ""):
            normalized[key] = value
            continue
        previous = normalized[key]
        if key in {"journal", "volume", "number", "year"} and isinstance(
            previous, list
        ):
            previous.append(value)
            continue
        if key in {"journal", "volume", "number", "year"} and previous != value:
            normalized[key] = [previous, value]
            continue
        if isinstance(previous, list):
            previous.append(value)
        elif previous != value:
            normalized[key] = [previous, value]
    return normalized


def normalize_source_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize a table of records while assigning standard bibliography fields."""
    normalized = []
    for row in rows:
        record = normalize_source_record(row, format="csv")
        normalized.append(record)
    return normalized


def normalize_format(value: str) -> str:
    name = value.lower().lstrip(".")
    name = ALIASES.get(name, name)
    if name not in READ_FORMATS:
        raise UnsupportedFormatError(f"Unsupported bibliography format: {value}")
    return name


def normalize_records(records: Any) -> OrderedDict[str, dict[str, Any]]:
    if not hasattr(records, "items"):
        raise RecordValidationError("records must be a mapping of IDs to records")
    output: OrderedDict[str, dict[str, Any]] = OrderedDict()
    used: set[str] = set()
    for mapping_id, raw in records.items():
        if not isinstance(raw, dict):
            raise RecordValidationError(f"record {mapping_id!r} must be a mapping")
        record = dict(raw)
        record = normalize_source_record(record)
        record_id = record.get("ID", mapping_id)
        if record_id is None or str(record_id).strip() == "":
            candidate = 1
            while str(candidate) in used:
                candidate += 1
            record_id = str(candidate)
        record_id = str(record_id)
        if record_id in used:
            raise DuplicateRecordIDError(f"Duplicate record ID: {record_id}")
        record["ID"] = record_id
        entrytype = record.get("ENTRYTYPE", "misc")
        if not isinstance(entrytype, str) or not entrytype.strip():
            raise RecordValidationError(
                f"record {record_id!r} has an invalid ENTRYTYPE"
            )
        record["ENTRYTYPE"] = entrytype.lower()
        used.add(record_id)
        output[record_id] = record
    return output


def _records_from_loaded_list(
    items: list[dict[str, Any]],
    *,
    allow_duplicate_ids: bool = False,
    generate_ids: bool = False,
) -> OrderedDict[str, dict[str, Any]]:
    """Build records from a parsed source, optionally retaining duplicate IDs.

    The first occurrence keeps its source ID as the mapping key. Subsequent
    occurrences get a unique mapping key while the record's ``ID`` remains the
    original source value. Strict input formats still reject duplicate IDs.
    """
    output: OrderedDict[str, dict[str, Any]] = OrderedDict()
    counts: dict[str, int] = {}
    for index, raw in enumerate(items, start=1):
        if not isinstance(raw, dict):
            raise ParseError("Each record must be a mapping")
        record = normalize_source_record(dict(raw))
        if generate_ids:
            record.pop("ID", None)
        source_id = None if generate_ids else record.get("ID")
        if source_id is None or str(source_id).strip() == "":
            source_id = str(index)
        source_id = str(source_id)
        if generate_ids:
            source_id = str(index)
        occurrence = counts.get(source_id, 0) + 1 if allow_duplicate_ids else 1
        counts[source_id] = occurrence
        key = source_id if occurrence == 1 else f"{source_id}#{occurrence}"
        if not allow_duplicate_ids and key in output:
            raise DuplicateRecordIDError(f"Duplicate record ID: {source_id}")
        while allow_duplicate_ids and key in output:
            occurrence += 1
            counts[source_id] = occurrence
            key = f"{source_id}#{occurrence}"
        if key in output:
            raise DuplicateRecordIDError(f"Duplicate record ID: {source_id}")
        record["ID"] = source_id
        entrytype = record.get("ENTRYTYPE", "misc")
        if not isinstance(entrytype, str) or not entrytype.strip():
            raise RecordValidationError(
                f"record {source_id!r} has an invalid ENTRYTYPE"
            )
        record["ENTRYTYPE"] = entrytype.lower()
        output[key] = record
    return output


def _records_from_list(items: Any) -> OrderedDict[str, dict[str, Any]]:
    if not isinstance(items, list):
        raise ParseError("Expected a list of record objects")
    pending = []
    source_ids = {
        str(item["ID"])
        for item in items
        if isinstance(item, dict) and item.get("ID") not in (None, "")
    }
    used: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise ParseError("Each record must be a JSON object")
        record = normalize_source_record(dict(item))
        record_id = record.get("ID")
        if not record_id:
            n = 1
            while str(n) in source_ids or str(n) in used:
                n += 1
            record_id = str(n)
        record["ID"] = str(record_id)
        if record["ID"] in used:
            raise DuplicateRecordIDError(f"Duplicate record ID: {record['ID']}")
        used.add(record["ID"])
        pending.append(record)
    return _records_from_loaded_list(pending)


def _decode_structured_bib_value(value: str, field: str) -> Any:
    """Decode a versioned JSON value stored in a declared BibTeX field."""
    if not value.startswith(_STRUCTURED_BIB_PREFIX):
        raise ParseError(
            f"BibTeX field {field!r} is declared structured but does not use "
            f"the {_STRUCTURED_BIB_PREFIX!r} encoding"
        )
    encoded = value[len(_STRUCTURED_BIB_PREFIX) :]
    try:
        payload = base64.b64decode(encoded, validate=True).decode("utf-8")
        result = json.loads(payload)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ParseError(
            f"Malformed structured value in BibTeX field {field!r}"
        ) from exc
    if not isinstance(result, (dict, list)):
        raise ParseError(
            f"Structured BibTeX field {field!r} must decode to a mapping or list"
        )
    return result


def _bib_records(
    text: str, *, mapping_fields: frozenset[str], list_fields: frozenset[str]
) -> OrderedDict[str, dict[str, Any]]:
    parsed = []
    for entry in re.finditer(r"@([\w-]+)\s*[{(]\s*([^,\s]+)\s*,", text):
        start = entry.end()
        depth, brace, quoted, escaped, end = 1, 0, False, False, start
        opening = text[entry.start() : entry.end()].rstrip()[-1]
        closing = "}" if opening == "{" else ")"
        while end < len(text):
            char = text[end]
            if char == '"' and not escaped and brace == 0:
                quoted = not quoted
            elif not quoted:
                if char == "{":
                    brace += 1
                elif char == "}" and brace:
                    brace -= 1
                elif brace == 0 and char == closing:
                    depth -= 1
                    if depth == 0:
                        break
                elif brace == 0 and char == "(":
                    depth += 1
                elif brace == 0 and char == ")" and closing == ")":
                    depth -= 1
                    if depth == 0:
                        break
            escaped = char == "\\" and not escaped
            if char != "\\":
                escaped = False
            end += 1
        body = text[start:end]
        record: dict[str, Any] = {
            "ID": entry.group(2),
            "ENTRYTYPE": entry.group(1).lower(),
        }
        if "#" in record["ID"]:
            record["ID"] = record["ID"].rsplit("#", 1)[0]
        for field in re.finditer(
            r"([\w-]+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|\"(?:[^\"]|\\.)*\"|[^,\s]+)\s*,?",
            body,
            re.S,
        ):
            value = field.group(2).strip()
            if (
                value.startswith("{")
                and value.endswith("}")
                or value.startswith('"')
                and value.endswith('"')
            ):
                value = value[1:-1]
            field_name = field.group(1).lower()
            value = value.strip()
            if field_name in mapping_fields | list_fields:
                if not field.group(2).strip().startswith("{"):
                    raise ParseError(
                        f"Structured BibTeX field {field_name!r} must use a braced value"
                    )
                value = value.lstrip("{").rstrip("}")
                prefix_index = value.find(_STRUCTURED_BIB_PREFIX)
                if prefix_index >= 0:
                    value = value[prefix_index:]
            if field_name in mapping_fields:
                decoded = _decode_structured_bib_value(value, field_name)
                if not isinstance(decoded, dict):
                    raise ParseError(
                        f"BibTeX field {field_name!r} was declared as a mapping "
                        "field but does not decode to a mapping"
                    )
                record[field_name] = decoded
            elif field_name in list_fields:
                decoded = _decode_structured_bib_value(value, field_name)
                if not isinstance(decoded, list):
                    raise ParseError(
                        f"BibTeX field {field_name!r} was declared as a list "
                        "field but does not decode to a list"
                    )
                record[field_name] = decoded
            else:
                record[field_name] = value
        parsed.append(normalize_source_record(record, format="bib"))
    if text.strip() and not parsed:
        raise ParseError("No BibTeX entries found")
    return _records_from_loaded_list(parsed, allow_duplicate_ids=True)


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
RIS_TYPE = {
    "JOUR": "article",
    "CONF": "inproceedings",
    "CPAPER": "inproceedings",
    "BOOK": "book",
    "CHAP": "inbook",
    "THES": "phdthesis",
    "RPRT": "techreport",
}


def _ris_records(text: str) -> OrderedDict[str, dict[str, Any]]:
    parsed = []
    record: dict[str, Any] = {}
    for line in text.splitlines() + ["ER  - "]:
        match = re.match(r"^\s*([A-Z0-9]{2,4})\s+-\s?(.*)$", line)
        if not match:
            continue
        tag, value = match.groups()
        if tag == "TY":
            record = {"ENTRYTYPE": RIS_TYPE.get(value.upper(), "misc")}
        elif tag == "VO":
            record["volume"] = value
        elif tag == "JA":
            record["journal_abbreviation"] = value
        elif tag == "ER":
            if record:
                record["ID"] = record.get("ID") or str(len(parsed) + 1)
                parsed.append(record)
            record = {}
        elif tag == "ID":
            record["ID"] = value
        else:
            key = RIS_MAP.get(tag, normalize_field_name(tag))
            if key in record:
                record[key] = (
                    [*record[key], value]
                    if isinstance(record[key], list)
                    else [record[key], value]
                )
            else:
                record[key] = value
    for item in parsed:
        start_page, end_page = item.pop("startpage", None), item.pop("endpage", None)
        if start_page is not None:
            item["pages"] = str(start_page) + (f"--{end_page}" if end_page else "")
        if isinstance(item.get("author"), list):
            item["author"] = " and ".join(item["author"])
    if text.strip() and not parsed:
        raise ParseError("No RIS records found")
    return _records_from_loaded_list(parsed)


def parse(
    text: str,
    format: str,
    *,
    mapping_fields: frozenset[str] = frozenset(),
    list_fields: frozenset[str] = frozenset(),
) -> OrderedDict[str, dict[str, Any]]:
    fmt = normalize_format(format)
    try:
        if fmt == "json":
            return _records_from_list(json.loads(text))
        if fmt == "csv":
            rows = list(csv.DictReader(StringIO(text)))
            return _records_from_loaded_list(
                normalize_source_rows(rows),
                generate_ids=True,
            )
        if fmt == "bib":
            return _bib_records(
                text, mapping_fields=mapping_fields, list_fields=list_fields
            )
        if fmt == "ris":
            return _ris_records(text)
        if fmt in {"md"}:
            raise OptionalBackendUnavailableError(
                "Markdown reference-list parsing requires an installed bibliography_io.backends 'markdown' backend"
            )
        if fmt in {"nbib", "enl", "txt"}:
            return _tagged_records(text, fmt)
    except (ParseError, OptionalBackendUnavailableError):
        raise
    except Exception as exc:
        raise ParseError(f"Could not parse {fmt} input: {exc}") from exc
    raise UnsupportedFormatError(f"Reading {fmt} is unsupported")


def _tagged_records(text: str, fmt: str) -> OrderedDict[str, dict[str, Any]]:
    parsed = []
    current: dict[str, Any] = {}
    for line in text.splitlines() + (["ER  -"] if fmt == "nbib" else [""]):
        if fmt == "nbib":
            match = re.match(r"^([A-Z0-9]{2,4})\s+-\s+(.*)$", line)
            if not line.strip() and current:
                current.setdefault("ENTRYTYPE", "article")
                current.setdefault("ID", str(len(parsed) + 1))
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
                        current.setdefault("ID", str(len(parsed) + 1))
                        parsed.append(current)
                        current = {}
                elif tag == "PMID":
                    current["pmid"] = value
                elif tag == "PT":
                    current["type"] = normalize_field_name(value)
                else:
                    current.setdefault(
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
                        }.get(tag, normalize_field_name(tag)),
                        value,
                    )
                continue
            if not line.strip() and current:
                current.setdefault("ENTRYTYPE", "article")
                current.setdefault("ID", str(len(parsed) + 1))
                parsed.append(current)
                current = {}
                continue
            if not line.strip() and not current:
                continue
        elif fmt != "nbib":
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
                current.setdefault("ID", str(len(parsed) + 1))
                parsed.append(current)
                current = {}
    if fmt == "nbib" and current:
        current.setdefault("ENTRYTYPE", "article")
        current.setdefault("ID", str(len(parsed) + 1))
        parsed.append(current)
    if text.strip() and not parsed:
        raise ParseError(f"No {fmt.upper()} records found")
    normalized = [normalize_source_record(row, format=fmt) for row in parsed]
    return _records_from_loaded_list(normalized, generate_ids=(fmt == "nbib"))


def _bib_escape(value: Any) -> str:
    if isinstance(value, (dict, list, tuple, set)):
        raise SerializationError(f"Cannot serialize non-scalar BibTeX value: {value!r}")
    return "{" + str(value).replace("}", r"\}") + "}"


def _encode_structured_bib_value(value: Any, field: str) -> str:
    """Encode mappings/lists as deterministic ASCII-safe JSON in a BibTeX value."""
    try:
        payload = json.dumps(
            value,
            ensure_ascii=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise SerializationError(
            f"Cannot serialize structured BibTeX field {field!r}: {exc}"
        ) from exc
    return _STRUCTURED_BIB_PREFIX + base64.b64encode(payload).decode("ascii")


def serialize(
    records: Any,
    format: str,
    *,
    mapping_fields: frozenset[str] = frozenset(),
    list_fields: frozenset[str] = frozenset(),
) -> str:
    fmt = normalize_format(format)
    if fmt not in WRITE_FORMATS:
        raise UnsupportedFormatError(f"Writing {fmt} is unsupported")
    data = normalize_records(records)
    if fmt == "json":
        return json.dumps(list(data.values()), ensure_ascii=False, indent=2)
    if fmt == "csv":
        fields = list(dict.fromkeys(k for record in data.values() for k in record))
        stream = StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(data.values())
        return stream.getvalue()
    if fmt == "bib":
        entries = []
        for record in data.values():
            fields = []
            for key, value in record.items():
                if key in {"ID", "ENTRYTYPE"}:
                    continue
                field_name = key.lower()
                if field_name in mapping_fields | list_fields:
                    expected_type = dict if field_name in mapping_fields else list
                    expected_label = "mapping" if expected_type is dict else "list"
                    if not isinstance(value, expected_type):
                        raise SerializationError(
                            f"BibTeX field {key!r} was declared as a {expected_label} "
                            f"field but has value {value!r}"
                        )
                    fields.append(
                        f"  {key} = {{{_encode_structured_bib_value(value, key)}}}"
                    )
                else:
                    fields.append(f"  {key} = {_bib_escape(value)}")
            entries.append(
                f"@{record['ENTRYTYPE']}{{{record['ID']},\n"
                + ",\n".join(fields)
                + "\n}"
            )
        return "\n\n".join(entries)
    if fmt == "ris":
        reverse = {v: k for k, v in RIS_MAP.items()}
        lines = []
        for record in data.values():
            typ = {
                "article": "JOUR",
                "inproceedings": "CONF",
                "book": "BOOK",
                "inbook": "CHAP",
            }.get(record["ENTRYTYPE"], "GEN")
            lines.append(f"TY  - {typ}")
            for key, value in record.items():
                if key in {"ID", "ENTRYTYPE"}:
                    continue
                values = value if isinstance(value, list) else [value]
                tag = reverse.get(key, key.upper()[:2])
                lines.extend(f"{tag}  - {item}" for item in values)
            lines.extend([f"ID  - {record['ID']}", "ER  - ", ""])
        return "\n".join(lines).rstrip()
    if fmt == "md":
        keys = list(dict.fromkeys(key for row in data.values() for key in row))

        def esc(value: Any) -> str:
            return str(value).replace("|", r"\|").replace("\n", " ")

        return (
            "| "
            + " | ".join(keys)
            + " |\n| "
            + " | ".join("---" for _ in keys)
            + " |\n"
            + "\n".join(
                "| " + " | ".join(esc(row.get(k, "")) for k in keys) + " |"
                for row in data.values()
            )
        )
    raise UnsupportedFormatError(f"Writing {fmt} is unsupported")
