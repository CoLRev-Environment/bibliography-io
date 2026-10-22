"""Standalone bibliographic record input and output."""

from __future__ import annotations

import warnings
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
from .normalization import normalize_format
from .normalization import normalize_records


def serialize(
    records: Any,
    format: str,
    *,
    mapping_fields: frozenset[str] = frozenset(),
    list_fields: frozenset[str] = frozenset(),
) -> str:
    """Serialize records by dispatching to the format-specific writer."""
    from .writers import serialize as dispatch

    return dispatch(
        records, format, mapping_fields=mapping_fields, list_fields=list_fields
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
    fmt: str,
    mapping_fields: Any,
    list_fields: Any,
) -> tuple[frozenset[str], frozenset[str]]:
    """Validate and normalize explicitly-declared structured field names."""
    if fmt != "bib":
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


def loads(
    text: str,
    *,
    format: str,
    mapping_fields: Any = (),
    list_fields: Any = (),
) -> list[dict[str, Any]]:
    """Load raw records from text, preserving order and source IDs.

    For BibTeX, ``mapping_fields`` and ``list_fields`` declare field names whose
    values use bibliography-io's versioned structured-value encoding. Supplying
    either option for other formats raises :class:`UnsupportedFormatError`.
    Declared field names match the lowercased BibTeX names.
    """
    if not isinstance(text, str):
        raise TypeError("text must be str")
    fmt = normalize_format(format)
    mappings, lists = _structured_fields(fmt, mapping_fields, list_fields)
    from .loaders import load_text

    return load_text(
        text, fmt, mapping_fields=mappings, list_fields=lists, source="<string>"
    )


def load_records(
    path: str | Path,
    *,
    format: str | None = None,
    mapping_fields: Any = (),
    list_fields: Any = (),
) -> list[dict[str, Any]]:
    """Load raw records as an ordered list; infer format from the suffix by default.

    A missing path raises :class:`FileNotFoundError`. For BibTeX, callers may
    declare structured fields with ``mapping_fields`` and ``list_fields``;
    these options are unsupported for other formats.
    """
    source = Path(path)
    fmt = _format_from_path(source, format)
    mappings, lists = _structured_fields(fmt, mapping_fields, list_fields)
    if not source.is_file():
        raise FileNotFoundError(source)
    if fmt in {"xls", "xlsx"}:
        from .loaders.tabular import load_excel

        return load_excel(source, fmt)
    text = source.read_text(encoding="utf-8-sig")
    from .loaders import load_text

    return load_text(
        text, fmt, mapping_fields=mappings, list_fields=lists, source=source
    )


def dumps(
    records: Any,
    *,
    format: str,
    mapping_fields: Any = (),
    list_fields: Any = (),
) -> str:
    """Serialize records to text.

    For BibTeX, ``mapping_fields`` and ``list_fields`` declare fields to encode
    as structured values. Supplying either option for other formats raises
    :class:`UnsupportedFormatError`. The declared names match the record field
    names (matching is case-insensitive, as BibTeX field names are).
    """
    fmt = normalize_format(format)
    mappings, lists = _structured_fields(fmt, mapping_fields, list_fields)
    if fmt in {"xlsx", "xls"}:
        raise UnsupportedFormatError(
            "Excel is a file format and cannot be serialized to text"
        )
    return serialize(records, fmt, mapping_fields=mappings, list_fields=lists)


def write_records(
    records: Any,
    *,
    path: str | Path,
    format: str | None = None,
    mapping_fields: Any = (),
    list_fields: Any = (),
) -> None:
    """Write records, replacing existing contents.

    For BibTeX, ``mapping_fields`` and ``list_fields`` declare fields to encode
    as structured values. Supplying either option for other formats raises
    :class:`UnsupportedFormatError`.
    """
    destination = Path(path)
    fmt = _format_from_path(destination, format)
    mappings, lists = _structured_fields(fmt, mapping_fields, list_fields)
    normalized = normalize_records(records)
    if fmt == "xlsx":
        try:
            import pandas as pd

            pd.DataFrame(normalized.values()).to_excel(destination, index=False)
        except ImportError as exc:
            raise OptionalBackendUnavailableError(
                "Writing Excel files requires Excel dependencies. Install them with "
                "'pip install bibliography-io[excel]'."
            ) from exc
        return
    if fmt == "md":
        output = _markdown_table(normalized)
    else:
        output = serialize(normalized, fmt, mapping_fields=mappings, list_fields=lists)
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


def _deprecated(name: str) -> None:
    warnings.warn(
        f"bibliography_io.{name} is deprecated; use the strict core API instead.",
        DeprecationWarning,
        stacklevel=3,
    )


def load(path: str | Path | None = None, **kwargs: Any) -> list[dict[str, Any]]:
    """Deprecated alias for :func:`load_records` without legacy CoLRev options."""
    _deprecated("load")
    if path is None:
        path = kwargs.pop("filename", None)
    if path is None:
        raise TypeError("load() requires a path")
    legacy_options = {
        "entrytype_setter",
        "field_mapper",
        "id_labeler",
        "unique_id_field",
        "logger",
        "empty_if_file_not_exists",
        "format_names",
    }
    unsupported = legacy_options & kwargs.keys()
    if unsupported:
        raise TypeError(
            "CoLRev-specific load options are no longer supported by "
            f"bibliography_io.load(): {', '.join(sorted(unsupported))}"
        )
    return load_records(path, **kwargs)


def write(records: Any, path: str | Path | None = None, **kwargs: Any) -> None:
    """Deprecated alias for :func:`write_records`."""
    _deprecated("write")
    if path is None and "filename" in kwargs:
        path = kwargs.pop("filename")
    if path is None:
        raise TypeError("write() requires a path")
    if kwargs:
        raise TypeError(f"Unexpected legacy write options: {', '.join(kwargs)}")
    write_records(records, path=path)


def write_file(records: Any, path: str | Path | None = None, **kwargs: Any) -> None:
    """Deprecated alias for :func:`write_records`."""
    _deprecated("write_file")
    if path is None:
        path = kwargs.pop("filename", None)
    if path is None or kwargs:
        raise TypeError("write_file() requires only records and path")
    write_records(records, path=path)


def to_string(*, records_dict: Any, implementation: str, **kwargs: Any) -> str:
    """Deprecated alias for :func:`dumps`."""
    _deprecated("to_string")
    if kwargs:
        raise TypeError(f"Unexpected legacy options: {', '.join(kwargs)}")
    return dumps(records_dict, format=implementation)


def load_df(filename: str | Path):
    """Deprecated convenience function returning a pandas DataFrame."""
    _deprecated("load_df")
    import pandas as pd

    return pd.DataFrame.from_dict(load_records(filename), orient="index")


def get_nr_records(filename: str | Path) -> int:
    """Deprecated convenience function counting records in a file."""
    _deprecated("get_nr_records")
    return len(load_records(filename))


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
    "dumps",
    "load_records",
    "loads",
    "write_records",
]
