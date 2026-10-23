"""Format-independent bibliography record and field normalization."""

from __future__ import annotations

import re
from collections import OrderedDict
from collections.abc import Mapping
from typing import Any

from .exceptions import DuplicateRecordIDError
from .exceptions import ParseError
from .exceptions import RecordValidationError
from .exceptions import UnsupportedFormatError

READ_FORMATS = {"bib", "ris", "csv", "xls", "xlsx", "enl", "txt", "nbib", "json", "md"}
ALIASES = {"bibtex": "bib", "markdown": "md", "excel": "xlsx", "endnote": "enl"}

_TABLE_FORMATS = {"csv", "xlsx", "xls"}


def normalize_field_name(
    value: str,
    *,
    field_aliases: Mapping[str, str] | None = None,
    preserve_dots: bool = False,
) -> str:
    """Normalize a label and optionally apply aliases keyed by normalized names."""
    pattern = r"[^a-z0-9.]+" if preserve_dots else r"[^a-z0-9]+"
    name = re.sub(pattern, "_", value.strip().lower()).strip("_")
    name = re.sub(r"_+", "_", name)
    return field_aliases.get(name, name) if field_aliases is not None else name


def normalize_source_record(
    record: dict[str, Any],
    *,
    format: str | None = None,
    field_aliases: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Normalize a source record using optional aliases and combine duplicates."""
    normalized: dict[str, Any] = {}
    raw_entrytype = record.get("ENTRYTYPE")
    for field, value in record.items():
        if field in {"ID", "ENTRYTYPE"}:
            normalized[field] = value
            continue
        if str(field).lower() == "entrytype":
            normalized["ENTRYTYPE"] = value
            continue
        key = normalize_field_name(
            str(field),
            field_aliases=field_aliases,
            preserve_dots=format == "bib",
        )
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
        elif key in {"journal", "volume", "number", "year"} and previous != value:
            normalized[key] = [previous, value]
        elif isinstance(previous, list):
            previous.append(value)
        elif previous != value:
            normalized[key] = [previous, value]
    return normalized


def normalize_source_rows(
    rows: list[dict[str, Any]],
    *,
    field_aliases: Mapping[str, str] | None = None,
    format: str = "csv",
) -> list[dict[str, Any]]:
    """Normalize table rows while assigning standard bibliography fields."""
    return [
        normalize_source_record(row, format=format, field_aliases=field_aliases)
        for row in rows
    ]


def normalize_format(value: str) -> str:
    """Normalize a format name or alias and validate that it is supported."""
    name = value.lower().lstrip(".")
    name = ALIASES.get(name, name)
    if name not in READ_FORMATS:
        raise UnsupportedFormatError(f"Unsupported bibliography format: {value}")
    return name


def normalize_records(
    records: Any,
    *,
    field_aliases: Mapping[str, str] | None = None,
    format: str | None = None,
) -> OrderedDict[str, dict[str, Any]]:
    """Validate output records and key them by unique IDs.

    ``field_aliases`` is opt-in so source-specific names are not inferred for
    records that have no known source format.
    """
    if isinstance(records, list):
        output: OrderedDict[str, dict[str, Any]] = OrderedDict()
        for index, raw in enumerate(records, start=1):
            if not isinstance(raw, dict):
                raise RecordValidationError(
                    f"record at position {index} must be a mapping"
                )
            record = normalize_source_record(
                dict(raw), format=format, field_aliases=field_aliases
            )
            record_id = record.get("ID")
            if record_id is None or str(record_id).strip() == "":
                record_id = str(index)
                record["ID"] = record_id
            record_id = str(record_id)
            record.setdefault("ENTRYTYPE", "misc")
            if (
                not isinstance(record["ENTRYTYPE"], str)
                or not record["ENTRYTYPE"].strip()
            ):
                raise RecordValidationError(
                    f"record {record_id!r} has an invalid ENTRYTYPE"
                )
            record["ENTRYTYPE"] = record["ENTRYTYPE"].lower()
            key, suffix = record_id, 2
            while key in output:
                key = f"{record_id}#{suffix}"
                suffix += 1
            output[key] = record
        return output
    if not hasattr(records, "items"):
        raise RecordValidationError("records must be a mapping of IDs to records")
    output = OrderedDict()
    used: set[str] = set()
    for mapping_id, raw in records.items():
        if not isinstance(raw, dict):
            raise RecordValidationError(f"record {mapping_id!r} must be a mapping")
        record = normalize_source_record(
            dict(raw), format=format, field_aliases=field_aliases
        )
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
    field_aliases: Mapping[str, str] | None = None,
    format: str | None = None,
) -> list[dict[str, Any]]:
    """Validate parsed records without altering IDs or collapsing duplicates."""
    output = []
    for raw in items:
        if not isinstance(raw, dict):
            raise ParseError("Each record must be a mapping")
        record = normalize_source_record(
            dict(raw), format=format, field_aliases=field_aliases
        )
        entrytype = record.get("ENTRYTYPE", "misc")
        if not isinstance(entrytype, str) or not entrytype.strip():
            raise RecordValidationError(
                f"record {record.get('ID')!r} has an invalid ENTRYTYPE"
            )
        record["ENTRYTYPE"] = entrytype.lower()
        output.append(record)
    return output


def _records_from_un_normalized_list(items: Any) -> list[dict[str, Any]]:
    """Validate parsed mappings without changing their source-level values."""
    if not isinstance(items, list):
        raise ParseError("Expected a list of record objects")
    output = []
    for raw in items:
        if not isinstance(raw, dict):
            raise ParseError("Each record must be a mapping")
        output.append(dict(raw))
    return output


def normalize_loaded_records(
    records: list[dict[str, Any]],
    *,
    field_aliases: Mapping[str, str] | None = None,
    list_fields: frozenset[str] = frozenset(),
    format: str | None = None,
) -> list[dict[str, Any]]:
    """Return convenient scalar-valued raw records from parsed records."""
    output = []
    for raw in records:
        record = normalize_source_record(
            dict(raw), format=format, field_aliases=field_aliases
        )
        for field, value in list(record.items()):
            if (
                field in {"ID", "ENTRYTYPE"}
                or isinstance(value, Mapping)
                or field in list_fields
            ):
                continue
            if isinstance(value, (list, tuple, set)):
                values = value if not isinstance(value, set) else sorted(value)
            else:
                values = [value]
            unique = []
            for item in values:
                if item is None or str(item).strip() == "":
                    continue
                text = str(item)
                if text not in unique:
                    unique.append(text)
            if field == "author":
                record[field] = " and ".join(unique)
            elif field in {"keywords", "keyword"}:
                record[field] = "; ".join(unique)
            elif len(unique) > 1:
                # Conflicting scalar values are retained, in source order, as
                # a readable string rather than changing the field's type.
                record[field] = "; ".join(unique)
            else:
                if unique:
                    record[field] = unique[0]
                else:
                    del record[field]
        output.append(record)
    return output


def _records_from_list(
    items: Any, *, field_aliases: Mapping[str, str] | None = None
) -> list[dict[str, Any]]:
    """Validate a parsed JSON list before normalizing its records."""
    if not isinstance(items, list):
        raise ParseError("Expected a list of record objects")
    return _records_from_loaded_list(items, field_aliases=field_aliases)
