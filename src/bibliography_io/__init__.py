"""Standalone bibliographic record input and output."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from importlib.metadata import entry_points
from pathlib import Path
from tempfile import TemporaryDirectory
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
from .normalization import normalize_loaded_record_values
from .normalization import normalize_records
from .normalization import normalize_source_record
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


def _load_path_raw(
    path: Path,
    format_name: str,
    *,
    mappings: frozenset[str],
    lists: frozenset[str],
    text: str | None = None,
) -> list[dict[str, Any]]:
    """Parse a file into raw records, using path-based parsing for Excel."""
    if format_name in {"xls", "xlsx"}:
        from .loaders.tabular import load_excel

        return load_excel(path, format=format_name)

    if text is None:
        text = path.read_text(encoding="utf-8-sig")
    from .loaders import load_string

    return load_string(
        text,
        format_name,
        normalize=False,
        mapping_fields=mappings,
        list_fields=lists,
        location=path,
    )


def _normalize_without_source(
    records: list[dict[str, Any]],
    *,
    format_name: str,
    mapping_fields: frozenset[str] = frozenset(),
    list_fields: frozenset[str] = frozenset(),
) -> list[dict[str, Any]]:
    """Dispatch no-source normalization to the format-specific loader."""
    normalizer_options = {}
    if format_name == "ris":
        from .loaders.ris import normalize_without_source as format_normalizer

    elif format_name == "bib":
        from .loaders.bibtex import normalize_without_source as format_normalizer

        normalizer_options = {
            "mapping_fields": mapping_fields,
            "list_fields": list_fields,
        }

    elif format_name in {"csv", "xls", "xlsx"}:
        from .loaders.tabular import normalize_without_source as format_normalizer

    elif format_name in {"enl", "nbib", "txt"}:
        from .loaders.tagged import normalize_without_source as format_normalizer

    elif format_name == "json":
        from .loaders.json import normalize_without_source as format_normalizer

    elif format_name == "md":
        from .loaders.markdown import normalize_without_source as format_normalizer

    else:
        raise UnsupportedFormatError(
            f"No no-source normalizer is available for {format_name}"
        )

    if format_name in {"enl", "nbib", "txt"}:
        records = format_normalizer(records, format=format_name)
    else:
        records = format_normalizer(records, **normalizer_options)
    from .normalization import _records_from_loaded_list, normalize_loaded_records

    normalized = _records_from_loaded_list(records, format=format_name)
    return normalize_loaded_records(
        normalized,
        mapping_fields=mapping_fields,
        list_fields=list_fields,
        format=format_name,
    )


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
    mapping_fields: Any = (),
    list_fields: Any = (),
) -> list[dict[str, Any]]:
    """Load parser-level records from a string, preserving source order.

    For BibTeX, ``mapping_fields`` and ``list_fields`` declare provenance
    mappings and semicolon-delimited list fields. Supplying either option for
    other formats raises
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
        normalize=False,
        mapping_fields=mappings,
        list_fields=lists,
        location="<string>",
    )


def load_raw(
    path: str | Path,
    *,
    format: str | None = None,
    mapping_fields: Any = (),
    list_fields: Any = (),
) -> list[dict[str, Any]]:
    """Load parser-level records as an ordered list.

    The format is inferred from the suffix by default. A missing path raises
    :class:`FileNotFoundError`. For BibTeX, callers may
    declare structured fields with ``mapping_fields`` and ``list_fields``;
    these options are unsupported for other formats.
    """
    source = Path(path)
    format_name = _format_from_path(source, format)
    mappings, lists = _structured_fields(format_name, mapping_fields, list_fields)
    if not source.is_file():
        raise FileNotFoundError(source)
    return _load_path_raw(source, format_name, mappings=mappings, lists=lists)


def _source_plugin(source: str) -> Any:
    """Load a CoLRev search-source class by its endpoint identifier."""
    points = entry_points()
    candidates = (
        points.select(group="colrev", name="search_source")
        if hasattr(points, "select")
        else [
            point for point in points.get("colrev", []) if point.name == "search_source"
        ]
    )
    matches = []
    for point in candidates:
        try:
            endpoint_class = point.load()
        except Exception:
            # A broken or unavailable unrelated source package should not
            # prevent discovery of the requested endpoint.
            continue
        if getattr(endpoint_class, "endpoint", None) == source:
            matches.append(endpoint_class)

    if not matches:
        raise OptionalBackendUnavailableError(
            f"CoLRev search-source package {source!r} is not installed or could "
            "not be loaded. Install the package providing that endpoint."
        )
    if len(matches) > 1:
        raise BackendExecutionError(
            f"Multiple CoLRev search-source packages declare endpoint {source!r}"
        )
    return matches[0]


def _normalize_source_records(
    records: list[dict[str, Any]],
    *,
    plugin: Any,
    source: str,
    format_name: str,
    source_version: str | None,
) -> list[dict[str, Any]]:
    """Apply and validate a search-source plugin's normalization hook."""
    normalize_hook = getattr(plugin, "normalize", None)
    if normalize_hook is None:
        raise UnsupportedFormatError(
            f"Source plugin {source!r} does not provide a normalize hook"
        )
    try:
        normalized = normalize_hook(
            records, format=format_name, source_version=source_version
        )
    except (OptionalBackendUnavailableError, UnsupportedFormatError):
        raise
    except Exception as exc:
        raise BackendExecutionError(
            f"Source plugin {source!r} failed to normalize {format_name} records"
        ) from exc
    if not isinstance(normalized, Mapping) or any(
        not isinstance(record_id, str)
        or not record_id
        or not isinstance(record, dict)
        or record.get("ID") != record_id
        for record_id, record in normalized.items()
    ):
        raise RecordValidationError(
            "Search-source normalize() must return a mapping keyed by each "
            "record's non-empty ID"
        )
    records = [
        normalize_source_record(record, format=format_name)
        for record in normalized.values()
    ]
    for record in records:
        entrytype = record.get("ENTRYTYPE", "misc")
        if not isinstance(entrytype, str) or not entrytype.strip():
            raise RecordValidationError(
                f"record {record['ID']!r} has an invalid ENTRYTYPE"
            )
        record["ENTRYTYPE"] = entrytype.lower()
        normalize_loaded_record_values(record)
    return records


def _preprocess_source_file(
    plugin: Any,
    path: Path,
    *,
    format_name: str,
    source: str,
    source_version: str | None,
    output_dir: Path,
) -> Path:
    """Run a source file hook and validate its returned input path."""
    preprocess_file = getattr(plugin, "preprocess_file", None)
    if preprocess_file is None:
        return path
    try:
        preprocessed_path = preprocess_file(
            path,
            format=format_name,
            source_version=source_version,
            output_dir=output_dir,
        )
    except (OptionalBackendUnavailableError, UnsupportedFormatError):
        raise
    except Exception as exc:
        raise BackendExecutionError(
            f"Source plugin {source!r} failed to preprocess {format_name} file"
        ) from exc

    if not isinstance(preprocessed_path, (str, Path)):
        raise RecordValidationError(
            "Search-source preprocess_file() must return a file path"
        )
    preprocessed_path = Path(preprocessed_path)
    if not preprocessed_path.is_file():
        raise RecordValidationError(
            "Search-source preprocess_file() must return an existing file path"
        )
    original_path = path.resolve()
    returned_path = preprocessed_path.resolve()
    temporary_root = output_dir.resolve()
    if returned_path != original_path and not returned_path.is_relative_to(
        temporary_root
    ):
        raise RecordValidationError(
            "Search-source preprocess_file() must return the original path or a "
            "file under output_dir"
        )
    return preprocessed_path


def _load_text(
    text: str,
    *,
    format_name: str,
    source: str | None,
    source_version: str | None,
    location: str | Path,
) -> list[dict[str, Any]]:
    """Load text through built-in format or source-plugin normalization."""
    if not isinstance(text, str):
        raise TypeError("input must be a string")
    if source is not None and (not isinstance(source, str) or not source.strip()):
        raise RecordValidationError("source must be a non-empty string when supplied")
    if source_version is not None and not isinstance(source_version, str):
        raise RecordValidationError("source_version must be a string or None")
    mappings, lists = _structured_fields(format_name, (), ())
    from .loaders import load_string

    if source is None:
        return load_string(
            text,
            format_name,
            normalize=True,
            mapping_fields=mappings,
            list_fields=lists,
            location=location,
        )

    plugin = _source_plugin(source)
    preprocess = getattr(plugin, "preprocess", None)
    if preprocess is not None:
        try:
            text = preprocess(text, format=format_name, source_version=source_version)
        except (OptionalBackendUnavailableError, UnsupportedFormatError):
            raise
        except Exception as exc:
            raise BackendExecutionError(
                f"Source plugin {source!r} failed to preprocess {format_name} input"
            ) from exc
        if not isinstance(text, str):
            raise RecordValidationError("Search-source preprocess() must return text")
    records = load_string(
        text,
        format_name,
        normalize=False,
        mapping_fields=mappings,
        list_fields=lists,
        location=location,
    )
    return _normalize_source_records(
        records,
        plugin=plugin,
        source=source,
        format_name=format_name,
        source_version=source_version,
    )


def loads(
    text: str,
    *,
    format: str,
    source: str | None = None,
    source_version: str | None = None,
) -> list[dict[str, Any]]:
    """Load and normalize text using built-in format or source-plugin rules.

    ``format`` is required because the input has no file suffix. ``xls`` and
    ``xlsx`` are not supported because they require file-based input.
    """
    format_name = normalize_format(format)
    if format_name in {"xls", "xlsx"}:
        raise UnsupportedFormatError(f"Loading {format_name} from text is unsupported")
    return _load_text(
        text,
        format_name=format_name,
        source=source,
        source_version=source_version,
        location="<string>",
    )


def load(
    path: str | Path,
    *,
    source: str | None = None,
    source_version: str | None = None,
    format: str | None = None,
) -> list[dict[str, Any]]:
    """Load records with normalized field names and string values.

    The format is inferred from the file suffix unless ``format`` is supplied.
    Use ``format`` when the suffix is ambiguous or does not match the file's
    actual format. When ``source`` is supplied, it selects the CoLRev
    search-source package with the matching endpoint identifier and applies its
    preprocessing and normalization hooks. Otherwise, format-specific
    no-source normalization is applied. Both paths return string values for
    every field; repeated values are combined, and native non-string values
    are converted to strings. Use
    :func:`loads` for text input, or :func:`load_raw` and :func:`loads_raw` for
    parser-level records.
    """
    if source is not None and (not isinstance(source, str) or not source.strip()):
        raise RecordValidationError("source must be a non-empty string when supplied")
    if source_version is not None and not isinstance(source_version, str):
        raise RecordValidationError("source_version must be a string or None")
    source_path = Path(path)
    format_name = _format_from_path(source_path, format)
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    if source is None:
        if format_name in {"xls", "xlsx"}:
            mappings, lists = _structured_fields(format_name, (), ())
            records = _load_path_raw(
                source_path, format_name, mappings=mappings, lists=lists
            )
            return _normalize_without_source(
                records,
                format_name=format_name,
                mapping_fields=mappings,
                list_fields=lists,
            )
        string = source_path.read_text(encoding="utf-8-sig")
        return _load_text(
            string,
            format_name=format_name,
            source=None,
            source_version=source_version,
            location=source_path,
        )

    if format_name in {"xls", "xlsx"}:
        if not isinstance(source, str) or not source.strip():
            raise RecordValidationError(
                "source must be a non-empty string when supplied"
            )
        mappings, lists = _structured_fields(format_name, (), ())
        plugin = _source_plugin(source)
        with TemporaryDirectory(prefix="bibliography-io-") as temporary_directory:
            output_dir = Path(temporary_directory)
            preprocessed_path = _preprocess_source_file(
                plugin,
                source_path,
                format_name=format_name,
                source=source,
                source_version=source_version,
                output_dir=output_dir,
            )
            records = _load_path_raw(
                preprocessed_path, format_name, mappings=mappings, lists=lists
            )
            return _normalize_source_records(
                records,
                plugin=plugin,
                source=source,
                format_name=format_name,
                source_version=source_version,
            )
    string = source_path.read_text(encoding="utf-8-sig")
    return _load_text(
        string,
        format_name=format_name,
        source=source,
        source_version=source_version,
        location=source_path,
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
    format_name = normalize_format(format)
    mappings, lists = _structured_fields(format_name, mapping_fields, list_fields)
    from .loaders import load_string

    records = load_string(
        text,
        format_name,
        normalize=True,
        mapping_fields=mappings,
        list_fields=lists,
        location="<string>",
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
    """Load primary records as an ID-indexed dictionary.

    For BibTeX, ``header_only=True`` extracts ``ID``, ``ENTRYTYPE``,
    ``colrev_origin``, ``colrev_status``, ``file``, ``screening_criteria``,
    and ``colrev_masterdata_provenance`` while skipping other fields.
    Ordinary field values are strings. Declare fields through
    ``mapping_fields`` or ``list_fields`` to decode their BibTeX values into
    dictionaries or lists. Undeclared values remain strings.
    """
    if not isinstance(header_only, bool):
        raise TypeError("header_only must be a bool")
    source = Path(path)
    format_name = _format_from_path(source, format)
    if not source.is_file():
        return {}
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
            location=source,
            header_only=True,
        )
    else:
        if format_name in {"xls", "xlsx"}:
            records = _load_path_raw(
                source, format_name, mappings=mappings, lists=lists
            )
            records = _normalize_without_source(
                records,
                format_name=format_name,
                mapping_fields=mappings,
                list_fields=lists,
            )
            return _index_primary_records(records)
        string = source.read_text(encoding="utf-8-sig")
        from .loaders import load_string

        records = load_string(
            string,
            format_name,
            normalize=True,
            mapping_fields=mappings,
            list_fields=lists,
            location=source,
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


def load_df(
    path: str | Path,
    *,
    source: str | None = None,
    source_version: str | None = None,
    format: str | None = None,
) -> Any:
    """Load normalized records into a DataFrame.

    ``format`` overrides suffix inference when a file suffix is ambiguous or
    does not match the file's actual format. Source-specific normalization can
    be selected with ``source`` and ``source_version``.
    """
    records = load(path, source=source, source_version=source_version, format=format)
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
    if not Path(filename).is_file():
        return 0
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
    Inputs are sorted by record ID by default. CSV, Markdown, Excel, and RIS
    output always uses ID order; ``sort_by_id=False`` preserves input order only
    for formats that support it.
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
    are sorted by record ID by default. CSV, Markdown, Excel, and RIS output
    always uses ID order; ``sort_by_id=False`` preserves input order only for
    formats that support it. ``primary=True`` continues to sort the validated
    primary mapping by ID.
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
        from .writers.excel import write_excel

        write_excel(
            normalized,
            destination,
            sort_fields=sort_fields,
            sort_by_id=sort_by_id,
        )
        return
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


def update(
    path: str | Path,
    records: Mapping[str, Mapping[str, Any]],
    *,
    mapping_fields: Any = (),
    list_fields: Any = (),
    field_order: Any = None,
    sort_fields: bool = True,
) -> None:
    """Update primary BibTeX records in place, appending records not present.

    Existing entries with IDs in ``records`` are replaced; entries with other
    IDs are left untouched. Records are supplied as an ID-keyed mapping. This
    byte-scanning update assumes entry headers are on their own lines and that
    field text does not contain ``@`` at the start of a line.
    """
    if not isinstance(records, Mapping):
        raise RecordValidationError(
            "primary records must be a mapping of IDs to records"
        )
    if not isinstance(sort_fields, bool):
        raise TypeError("sort_fields must be a bool")
    values = list(records.values())
    if any(not isinstance(record, dict) for record in values):
        raise RecordValidationError("each primary record must be a mapping")
    _index_primary_records(values)
    for record_id, record in records.items():
        if record_id != record["ID"]:
            raise RecordValidationError(
                f"primary record mapping key {record_id!r} does not match its ID"
            )

    mappings, lists = _structured_fields("bib", mapping_fields, list_fields)
    ordered_fields = _normalize_field_order("bib", field_order)
    normalized = normalize_records(records, format="bib")
    if mappings:
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
    serialized = {
        record_id: (
            write_string(
                {record_id: record},
                "bib",
                mapping_fields=mappings,
                list_fields=lists,
                field_order=ordered_fields,
                sort_fields=sort_fields,
                sort_by_id=False,
            )
            + "\n"
        ).encode("utf-8")
        for record_id, record in sorted(normalized.items())
    }

    destination = Path(path)
    if destination.is_file():
        content = destination.read_bytes()
        starts: list[tuple[int, str]] = []
        offset = 0
        for line in content.splitlines(keepends=True):
            if b"@" in line[:3]:
                opening = line.find(b"{")
                comma = line.find(b",", opening + 1)
                if opening < 0 or comma < 0:
                    raise RecordValidationError("invalid BibTeX entry header")
                try:
                    record_id = line[opening + 1 : comma].decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise RecordValidationError(
                        "BibTeX entry IDs must be valid UTF-8"
                    ) from exc
                starts.append((offset, record_id))
            offset += len(line)

        updated = bytearray()
        cursor = 0
        for index, (start, record_id) in enumerate(starts):
            end = starts[index + 1][0] if index + 1 < len(starts) else len(content)
            if record_id in serialized:
                updated.extend(content[cursor:start])
                updated.extend(serialized.pop(record_id))
                cursor = end
        updated.extend(content[cursor:])
        destination.write_bytes(updated)

    if serialized:
        with destination.open("ab") as output:
            if destination.is_file() and destination.stat().st_size:
                with destination.open("rb") as current:
                    current.seek(-1, 2)
                    if current.read(1) not in {b"\n", b"\r"}:
                        output.write(b"\n")
            for record in serialized.values():
                output.write(record)


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
    "load",
    "load_df",
    "load_primary",
    "load_primary_df",
    "load_raw",
    "loads",
    "loads_primary",
    "loads_raw",
    "to_string",
    "update",
    "write",
]
