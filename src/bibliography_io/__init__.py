"""Public interface for loading and writing bibliographic records.

The CoLRev-backed load and write functions are imported only when called, so
the package itself can be imported without installing the ``colrev`` extra.
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Any
from typing import Callable


def _require_colrev() -> None:
    """Raise an actionable error when the optional CoLRev extra is absent."""
    if importlib.util.find_spec("colrev") is None:
        raise ImportError(
            "This operation requires CoLRev. Install it with "
            "`pip install 'bibliography-io[colrev]'`."
        )


def _load_utils() -> Any:
    _require_colrev()
    return importlib.import_module(".loader.load_utils", __name__)


def _write_utils() -> Any:
    _require_colrev()
    return importlib.import_module(".writer.write_utils", __name__)


def load_records(
    filename: Path,
    *,
    entrytype_setter: Callable[[dict], None] | None = None,
    field_mapper: Callable[[dict], None] | None = None,
    id_labeler: Callable = lambda x: x,
    unique_id_field: str = "",
    logger: logging.Logger = logging.getLogger(__name__),
    empty_if_file_not_exists: bool = True,
    format_names: bool = False,
) -> dict:
    """Load bibliographic records from a supported file."""
    return _load_utils().load(
        filename=filename,
        entrytype_setter=entrytype_setter,
        field_mapper=field_mapper,
        id_labeler=id_labeler,
        unique_id_field=unique_id_field,
        logger=logger,
        empty_if_file_not_exists=empty_if_file_not_exists,
        format_names=format_names,
    )


def loads(
    load_string: str,
    *,
    implementation: str,
    entrytype_setter: Callable[[dict], None] | None = None,
    field_mapper: Callable[[dict], None] | None = None,
    id_labeler: Callable = lambda x: x,
    unique_id_field: str = "",
    logger: logging.Logger = logging.getLogger(__name__),
) -> dict:
    """Load bibliographic records from a string."""
    return _load_utils().loads(
        load_string=load_string,
        implementation=implementation,
        entrytype_setter=entrytype_setter,
        field_mapper=field_mapper,
        id_labeler=id_labeler,
        unique_id_field=unique_id_field,
        logger=logger,
    )


def load_df(filename: Path) -> Any:
    """Load a file and return its records as a pandas DataFrame."""
    return _load_utils().load_df(filename=filename)


def get_nr_records(filename: Path) -> int:
    """Return the number of records in a supported file."""
    return _load_utils().get_nr_records(filename=filename)


def write_records(records_dict: dict, *, filename: Path, **kwargs: Any) -> dict:
    """Write records to a supported file."""
    return _write_utils().write_file(
        records_dict=records_dict,
        filename=filename,
        **kwargs,
    )


def to_string(*, records_dict: dict, implementation: str, **kwargs: Any) -> str:
    """Serialize records to a supported bibliographic format string."""
    return _write_utils().to_string(
        records_dict=records_dict,
        implementation=implementation,
        **kwargs,
    )


load = load_records
write = write_records
write_file = write_records

__all__ = [
    "get_nr_records",
    "load",
    "load_df",
    "load_records",
    "loads",
    "to_string",
    "write",
    "write_records",
    "write_file",
]
