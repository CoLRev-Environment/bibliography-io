#! /usr/bin/env python
"""Function to write files (BiBTeX, RIS, CSV, etc.).

Usage::

    import colrev.loader.load_utils
    import colrev.writer.write_utils

    # Load
    records = colrev.loader.load_utils.load(filename=filename)

    # Write
    colrev.writer.write_utils.write_file(records, filename=filename)

"""

from __future__ import annotations

from pathlib import Path

from . import bib as bib_writer
from . import csv as csv_writer
from . import excel as excel_writer
from . import markdown as markdown_writer
from . import ris as ris_writer


def write_file(records_dict: dict, *, filename: Path, **kw) -> dict:  # type: ignore
    """Write a file (BiBTex, RIS, or other) from a dictionary of records.

    Note:
        For tabular formats (csv, xlsx, md), the following options are supported:
            - sort_fields_first: list of fields to appear first in the output
            - drop_empty_fields: if True, empty fields will be omitted

    """
    if isinstance(filename, str):
        filename = Path(filename)
    if filename.suffix == ".bib":
        writer = bib_writer.write_file
    elif filename.suffix == ".ris":
        writer = ris_writer.write_file
    elif filename.suffix == ".csv":
        writer = csv_writer.write_file
    elif filename.suffix == ".xlsx":
        writer = excel_writer.write_file
    elif filename.suffix == ".md":
        writer = markdown_writer.write_file
    else:
        raise NotImplementedError(f"Unsupported file type: {filename.suffix}")

    kw["filename"] = filename
    kw["records_dict"] = records_dict

    writer(**kw)


def to_string(*, records_dict: dict, implementation: str, **kw) -> str:  # type: ignore
    """Write a string (BiBTex, RIS, or other) from a dictionary of records."""
    if implementation == "bib":
        writer = bib_writer.to_string
    elif implementation == "ris":
        writer = ris_writer.to_string
    else:
        raise NotImplementedError

    kw["records_dict"] = records_dict

    return writer(**kw)


# see https://github.com/MrTango/rispy/blob/main/rispy/parser.py
