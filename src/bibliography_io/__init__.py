"""Standalone bibliographic record input and output."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .exceptions import BackendExecutionError
from .exceptions import BibliographyIOError
from .exceptions import DuplicateRecordIDError
from .exceptions import MissingRecordIDError
from .exceptions import OptionalBackendUnavailableError
from .exceptions import ParseError
from .exceptions import RecordValidationError
from .exceptions import SerializationError
from .exceptions import UnsupportedFormatError
from .normalization import normalize_field_name
from .normalization import normalize_format
from .normalization import normalize_records
from .normalization import sort_records_by_id


def write_string(
    records: Any,
    format: str,
    *,
    mapping_fields: frozenset[str] = frozenset(),
    list_fields: frozenset[str] = frozenset(),
    field_order: Any = None,
    sort_fields: bool = True,
    sort_by_id: bool = True,
) -> str:
    """Write records to a formatted string using the format-specific writer."""
    if not isinstance(sort_fields, bool):
        raise TypeError("sort_fields must be a bool")
    if not isinstance(sort_by_id, bool):
        raise TypeError("sort_by_id must be a bool")
    from .writers import write_string as dispatch

    return dispatch(
        records,
        format,
        mapping_fields=mapping_fields,
        list_fields=list_fields,
        field_order=_normalize_field_order(normalize_format(format), field_order),
        sort_fields=sort_fields,
        sort_by_id=sort_by_id,
    )


def _format_from_path(path: str | Path, format: str | None) -> str:
    if format is not None:
        return normalize_format(format)
    suffix = Path(path).suffix
    if not suffix:
        raise UnsupportedFormatError(
            f"Cannot infer bibliography format from path: {path}"
        )
    return normalize_format(suffix)


def _structured_fields(
    format: str,
    mapping_fields: Any,
    list_fields: Any,
) -> tuple[frozenset[str], frozenset[str]]:
    """Validate and normalize explicitly-declared structured field names."""
    if format != "bib":
        try:
            has_fields = bool(mapping_fields) or bool(list_fields)
        except (TypeError, ValueError) as exc:
            raise RecordValidationError(
                "mapping_fields and list_fields must be iterables of field names"
            ) from exc
        if has_fields:
            raise UnsupportedFormatError(
                "mapping_fields and list_fields are only supported for BibTeX"
            )
        return frozenset(), frozenset()
    try:
        mappings = frozenset(mapping_fields)
        lists = frozenset(list_fields)
    except TypeError as exc:
        raise RecordValidationError(
            "mapping_fields and list_fields must be iterables of field names"
        ) from exc
    if any(not isinstance(field, str) or not field for field in mappings | lists):
        raise RecordValidationError(
            "mapping_fields and list_fields must contain non-empty strings"
        )
    overlap = mappings & lists
    if overlap:
        raise RecordValidationError(
            f"Fields cannot be declared as both mappings and lists: {sorted(overlap)}"
        )
    return mappings, lists


def _normalize_field_order(format: str, field_order: Any) -> tuple[str, ...] | None:
    """Validate and normalize an optional output field order."""
    if field_order is None:
        return None
    if format != "bib":
        raise UnsupportedFormatError("field_order is only supported for BibTeX")
    if isinstance(field_order, (str, bytes)) or not isinstance(field_order, Iterable):
        raise RecordValidationError("field_order must be an iterable of field names")
    fields = tuple(field_order)
    if any(not isinstance(field, str) or not field.strip() for field in fields):
        raise RecordValidationError(
            "field_order must contain non-empty string field names"
        )
    normalized = tuple(
        normalize_field_name(field, preserve_dots=True) for field in fields
    )
    if len(set(normalized)) != len(normalized):
        raise RecordValidationError("field_order must not contain duplicate fields")
    return normalized


def loads_raw(
    text: str,
    *,
    format: str,
    normalize: bool = True,
    mapping_fields: Any = (),
    list_fields: Any = (),
) -> list[dict[str, Any]]:
    """Load raw records from a string, preserving order and source IDs.

    By default, returns normalized raw data for convenient access. Set
    ``normalize=False`` to retain parser-level values for source-specific
    processing. For BibTeX, ``mapping_fields`` and ``list_fields`` declare
    provenance mappings and semicolon-delimited list fields. Supplying either
    option for other formats raises
    :class:`UnsupportedFormatError`. Declared field names match the lowercased
    BibTeX names.
    """
    if not isinstance(text, str):
        raise TypeError("input must be a string")
    format_name = normalize_format(format)
    mappings, lists = _structured_fields(format_name, mapping_fields, list_fields)
    from .loaders import load_string

    return load_string(
        text,
        format_name,
        normalize=normalize,
        mapping_fields=mappings,
        list_fields=lists,
        source="<string>",
    )


def load_raw(
    path: str | Path,
    *,
    format: str | None = None,
    normalize: bool = True,
    mapping_fields: Any = (),
    list_fields: Any = (),
) -> list[dict[str, Any]]:
    """Load raw records as an ordered list; infer format from the suffix by default.

    By default, returns normalized raw data for convenient access. Set
    ``normalize=False`` for parser-level values and source-specific processing.
    A missing path raises :class:`FileNotFoundError`. For BibTeX, callers may
    declare structured fields with ``mapping_fields`` and ``list_fields``;
    these options are unsupported for other formats.
    """
    source = Path(path)
    format_name = _format_from_path(source, format)
    mappings, lists = _structured_fields(format_name, mapping_fields, list_fields)
    if not source.is_file():
        raise FileNotFoundError(source)
    if format_name in {"xls", "xlsx"}:
        from .loaders.tabular import load_excel
        from .normalization import normalize_loaded_records

        records = load_excel(source, format=format_name, normalize=normalize)
        return (
            normalize_loaded_records(records, list_fields=lists)
            if normalize
            else records
        )
    string = source.read_text(encoding="utf-8-sig")
    from .loaders import load_string

    return load_string(
        string,
        format_name,
        normalize=normalize,
        mapping_fields=mappings,
        list_fields=lists,
        source=source,
    )


def _index_primary_records(
    records: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Validate primary record headers and index records by their IDs."""
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        record_id = record.get("ID")
        if not isinstance(record_id, str) or not record_id.strip():
            raise MissingRecordIDError("Primary records require a non-empty string ID")
        if record_id in indexed:
            raise DuplicateRecordIDError(f"Duplicate record ID: {record_id}")
        entrytype = record.get("ENTRYTYPE")
        if not isinstance(entrytype, str) or not entrytype.strip():
            raise RecordValidationError(
                f"record {record_id!r} has an invalid ENTRYTYPE"
            )
        indexed[record_id] = record
    return indexed


def loads_primary(
    text: str,
    *,
    format: str,
    mapping_fields: Any = (),
    list_fields: Any = (),
) -> dict[str, dict[str, Any]]:
    """Load primary records from a string as an ID-indexed dictionary."""
    records = loads_raw(
        text,
        format=format,
        mapping_fields=mapping_fields,
        list_fields=list_fields,
    )
    return _index_primary_records(records)


def load_primary(
    path: str | Path,
    *,
    format: str | None = None,
    header_only: bool = False,
    mapping_fields: Any = (),
    list_fields: Any = (),
) -> dict[str, dict[str, Any]]:
    """Load primary records from a file as an ID-indexed dictionary."""
    if not isinstance(header_only, bool):
        raise TypeError("header_only must be a bool")
    source = Path(path)
    format_name = _format_from_path(source, format)
    if not source.is_file():
        raise FileNotFoundError(source)
    mappings, lists = _structured_fields(format_name, mapping_fields, list_fields)
    if header_only and format_name != "bib":
        raise UnsupportedFormatError("header_only is only supported for BibTeX")
    if header_only:
        string = source.read_text(encoding="utf-8-sig")
        from .loaders import load_string

        records = load_string(
            string,
            format_name,
            mapping_fields=mappings,
            list_fields=lists,
            source=source,
            header_only=True,
        )
    else:
        records = load_raw(
            source,
            format=format_name,
            mapping_fields=mappings,
            list_fields=lists,
        )
    return _index_primary_records(records)


def _load_pandas() -> Any:
    """Import the optional DataFrame backend."""
    try:
        import pandas as pd
    except ImportError as exc:
        raise OptionalBackendUnavailableError(
            "Loading records as DataFrames requires pandas. Install it with "
            "'pip install bibliography-io[excel]'."
        ) from exc
    return pd


def load_raw_df(
    path: str | Path,
    *,
    format: str | None = None,
    normalize: bool = True,
    mapping_fields: Any = (),
    list_fields: Any = (),
) -> Any:
    """Load raw records into a DataFrame, preserving source order as rows."""
    records = load_raw(
        path,
        format=format,
        normalize=normalize,
        mapping_fields=mapping_fields,
        list_fields=list_fields,
    )
    pd = _load_pandas()
    return pd.DataFrame(records)


def load_primary_df(
    path: str | Path,
    *,
    format: str | None = None,
    header_only: bool = False,
    mapping_fields: Any = (),
    list_fields: Any = (),
) -> Any:
    """Load primary records into a DataFrame indexed by record ID."""
    records = load_primary(
        path,
        format=format,
        header_only=header_only,
        mapping_fields=mapping_fields,
        list_fields=list_fields,
    )
    pd = _load_pandas()
    return pd.DataFrame.from_dict(records, orient="index")


def get_nr_records(filename: str | Path) -> int:
    """Return the number of raw records in a file."""
    return len(load_raw(filename))


def to_string(
    records: Any,
    *,
    format: str,
    mapping_fields: Any = (),
    list_fields: Any = (),
    field_order: Any = None,
    sort_fields: bool = True,
    sort_by_id: bool = True,
) -> str:
    """Return records written as a formatted string.

    For BibTeX, ``mapping_fields`` and ``list_fields`` declare provenance
    mappings and semicolon-delimited list fields. Supplying either option for
    other formats raises
    :class:`UnsupportedFormatError`. The declared names match the record field
    names (matching is case-insensitive, as BibTeX field names are).
    By default, ``field_order`` (or the CoLRev-oriented order when omitted) is
    followed by remaining fields alphabetically. Set ``sort_fields=False`` to
    preserve the input field order without sorting.
    Inputs are sorted by record ID by default; set ``sort_by_id=False`` to
    preserve list order or mapping iteration order.
    """
    if not isinstance(sort_by_id, bool):
        raise TypeError("sort_by_id must be a bool")
    if not isinstance(sort_fields, bool):
        raise TypeError("sort_fields must be a bool")
    format_name = normalize_format(format)
    mappings, lists = _structured_fields(format_name, mapping_fields, list_fields)
    if format_name in {"xlsx", "xls"}:
        raise UnsupportedFormatError(
            "Excel is a file format and cannot be written as a string"
        )
    return write_string(
        records,
        format_name,
        mapping_fields=mappings,
        list_fields=lists,
        field_order=_normalize_field_order(format_name, field_order),
        sort_fields=sort_fields,
        sort_by_id=sort_by_id,
    )


def write(
    records: Any,
    *,
    path: str | Path,
    format: str | None = None,
    mapping_fields: Any = (),
    list_fields: Any = (),
    field_order: Any = None,
    sort_fields: bool = True,
    primary: bool = False,
    sort_by_id: bool = True,
) -> None:
    """Write records, replacing existing contents.

    For BibTeX, ``mapping_fields`` and ``list_fields`` declare provenance
    mappings and semicolon-delimited list fields. Supplying either option for
    other formats raises
    :class:`UnsupportedFormatError`. Set ``primary=True`` to validate an
    ID-keyed primary-record mapping, sort records by ID, and restrict output to
    BibTeX. By default, ``field_order`` (or the CoLRev-oriented order when
    omitted) is followed by remaining fields alphabetically. Set
    ``sort_fields=False`` to preserve input field order without sorting. Inputs
    are sorted by record ID by default; set
    ``sort_by_id=False`` to preserve list order or mapping iteration order.
    ``primary=True`` continues to sort the validated primary mapping by ID.
    """
    if not isinstance(primary, bool):
        raise TypeError("primary must be a bool")
    if not isinstance(sort_by_id, bool):
        raise TypeError("sort_by_id must be a bool")
    if not isinstance(sort_fields, bool):
        raise TypeError("sort_fields must be a bool")
    destination = Path(path)
    format_name = _format_from_path(destination, format)
    if primary:
        if format_name != "bib":
            raise UnsupportedFormatError(
                "Primary records can only be written as BibTeX"
            )
        if not isinstance(records, Mapping):
            raise RecordValidationError(
                "primary records must be a mapping of IDs to records"
            )
        values = list(records.values())
        if any(not isinstance(record, dict) for record in values):
            raise RecordValidationError("each primary record must be a mapping")
        _index_primary_records(values)
    mappings, lists = _structured_fields(format_name, mapping_fields, list_fields)
    ordered_fields = _normalize_field_order(format_name, field_order)
    normalized = normalize_records(
        records, format="bib" if format_name == "bib" else None
    )
    if primary and mappings:
        normalized = {
            record_id: {
                key: value
                for key, value in record.items()
                if not (
                    key.lower() in mappings and isinstance(value, dict) and not value
                )
            }
            for record_id, record in normalized.items()
        }
    if sort_by_id:
        normalized = sort_records_by_id(normalized)
    if primary:
        normalized = dict(sorted(normalized.items(), key=lambda item: item[1]["ID"]))
    if format_name == "xlsx":
        try:
            import pandas as pd

            pd.DataFrame(normalized.values()).to_excel(destination, index=False)
        except ImportError as exc:
            raise OptionalBackendUnavailableError(
                "Writing Excel files requires Excel dependencies. Install them with "
                "'pip install bibliography-io[excel]'."
            ) from exc
        return
    if format_name == "md":
        output = _markdown_table(normalized)
    else:
        output = write_string(
            normalized,
            format_name,
            mapping_fields=mappings,
            list_fields=lists,
            field_order=ordered_fields,
            sort_fields=sort_fields,
            sort_by_id=False,
        )
    destination.write_text(output, encoding="utf-8")


def _markdown_table(records: dict[str, dict[str, Any]]) -> str:
    fields = list(dict.fromkeys(key for record in records.values() for key in record))

    def clean(value: Any) -> str:
        return str(value).replace("|", r"\|").replace("\n", " ")

    lines = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    lines.extend(
        "| " + " | ".join(clean(record.get(key, "")) for key in fields) + " |"
        for record in records.values()
    )
    return "\n".join(lines)


__all__ = [
    "BackendExecutionError",
    "BibliographyIOError",
    "DuplicateRecordIDError",
    "MissingRecordIDError",
    "OptionalBackendUnavailableError",
    "ParseError",
    "RecordValidationError",
    "SerializationError",
    "UnsupportedFormatError",
    "get_nr_records",
    "load_primary",
    "load_primary_df",
    "load_raw",
    "load_raw_df",
    "loads_primary",
    "loads_raw",
    "to_string",
    "write",
]
