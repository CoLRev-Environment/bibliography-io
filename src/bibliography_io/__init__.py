"""Standalone bibliographic record input and output."""

from __future__ import annotations

import importlib
import warnings
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

from .core import normalize_format
from .core import normalize_records
from .core import parse
from .core import serialize
from .exceptions import BackendExecutionError
from .exceptions import BibliographyIOError
from .exceptions import DuplicateRecordIDError
from .exceptions import MissingRecordIDError
from .exceptions import OptionalBackendUnavailableError
from .exceptions import ParseError
from .exceptions import RecordValidationError
from .exceptions import SerializationError
from .exceptions import UnsupportedFormatError


def _format_from_path(path: str | Path, format: str | None) -> str:
    if format is not None:
        return normalize_format(format)
    suffix = Path(path).suffix
    if not suffix:
        raise UnsupportedFormatError(
            f"Cannot infer bibliography format from path: {path}"
        )
    return normalize_format(suffix)


def _markdown_backend(text: str, source: str | Path) -> Any:
    points = entry_points()
    matches = (
        points.select(group="bibliography_io.backends", name="markdown")
        if hasattr(points, "select")
        else points.get("bibliography_io.backends", [])
    )
    for point in matches:
        try:
            backend = point.load()
            result = (
                backend.loads(text, source=source)
                if hasattr(backend, "loads")
                else backend(text, source=source)
            )
            return normalize_records(result)
        except OptionalBackendUnavailableError:
            raise
        except Exception as exc:
            raise BackendExecutionError(
                "Markdown backend failed to parse references"
            ) from exc
    raise OptionalBackendUnavailableError(
        "Markdown reference-list parsing is optional. Install a backend providing "
        "the 'bibliography_io.backends' entry point named 'markdown'."
    )


def loads(text: str, *, format: str) -> dict[str, dict[str, Any]]:
    """Parse bibliographic records from text using an explicit format."""
    if not isinstance(text, str):
        raise TypeError("text must be str")
    fmt = normalize_format(format)
    if fmt == "md":
        return _markdown_backend(text, "<string>")
    return parse(text, fmt)


def load_records(
    path: str | Path, *, format: str | None = None
) -> dict[str, dict[str, Any]]:
    """Load records from a UTF-8 file; infer its format from the suffix by default.

    A missing path raises :class:`FileNotFoundError`.
    """
    source = Path(path)
    fmt = _format_from_path(source, format)
    if not source.is_file():
        raise FileNotFoundError(source)
    if fmt in {"xls", "xlsx"}:
        import pandas as pd

        try:
            rows = pd.read_excel(source).fillna("").to_dict(orient="records")
            return normalize_records({str(i + 1): row for i, row in enumerate(rows)})
        except Exception as exc:
            raise ParseError(f"Could not parse {fmt} file {source}: {exc}") from exc
    text = source.read_text(encoding="utf-8-sig")
    if fmt == "md":
        return _markdown_backend(text, source)
    return parse(text, fmt)


def dumps(records: Any, *, format: str) -> str:
    """Serialize records to text using an explicit format."""
    fmt = normalize_format(format)
    if fmt in {"xlsx", "xls"}:
        raise UnsupportedFormatError(
            "Excel is a file format and cannot be serialized to text"
        )
    return serialize(records, fmt)


def write_records(records: Any, path: str | Path, *, format: str | None = None) -> None:
    """Write records to a file, replacing existing contents."""
    destination = Path(path)
    fmt = _format_from_path(destination, format)
    normalized = normalize_records(records)
    if fmt == "xlsx":
        import pandas as pd

        pd.DataFrame(normalized.values()).to_excel(destination, index=False)
        return
    if fmt == "md":
        output = _markdown_table(normalized)
    else:
        output = serialize(normalized, fmt)
    destination.write_text(output, encoding="utf-8")


def _markdown_table(records: dict[str, dict[str, Any]]) -> str:
    fields = list(dict.fromkeys(key for record in records.values() for key in record))
    clean = lambda value: str(value).replace("|", r"\|").replace("\n", " ")
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


def load(path: str | Path | None = None, **kwargs: Any) -> dict:
    """Deprecated compatibility entry point for historical CoLRev options."""
    _deprecated("load")
    if path is None:
        path = kwargs.pop("filename", None)
    if path is None:
        raise TypeError("load() requires a path")
    if kwargs and set(kwargs) <= {
        "entrytype_setter",
        "field_mapper",
        "id_labeler",
        "unique_id_field",
        "logger",
        "empty_if_file_not_exists",
        "format_names",
    }:
        try:
            return importlib.import_module(".loader.load_utils", __name__).load(
                filename=path, **kwargs
            )
        except ImportError as exc:
            raise ImportError(
                "Legacy load options require the CoLRev compatibility adapter"
            ) from exc
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
    write_records(records, path)


def write_file(records: Any, path: str | Path | None = None, **kwargs: Any) -> None:
    """Deprecated alias for :func:`write_records`."""
    _deprecated("write_file")
    if path is None:
        path = kwargs.pop("filename", None)
    if path is None or kwargs:
        raise TypeError("write_file() requires only records and path")
    write_records(records, path)


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
