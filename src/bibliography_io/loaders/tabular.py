"""CSV and Excel bibliography loaders."""

from __future__ import annotations

import csv
from io import StringIO
from math import isnan
from pathlib import Path
from typing import Any

from ..exceptions import OptionalBackendUnavailableError
from ..exceptions import ParseError
from ..normalization import _records_from_un_normalized_list
from ..normalization import STANDARD_FIELDS
from ..normalization import normalize_field_name

TABULAR_FIELD_ALIASES = {
    "authors": "author",
    "issue": "number",
    "journalbook": "journal_book",
    "publication_year": "year",
    "publicationyear": "year",
}


def normalize_without_source(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply known tabular mappings while preserving unknown field names."""
    for index, record in enumerate(records, start=1):
        lowered = {}
        for key, value in record.items():
            original_name = str(key)
            lowered_name = normalize_field_name(original_name)
            known_name = (
                lowered_name in STANDARD_FIELDS
                or lowered_name in TABULAR_FIELD_ALIASES
                or lowered_name
                in {
                    "id",
                    "entrytype",
                    "type",
                    "authors",
                    "publication",
                    "category",
                    "affiliations",
                    "journal_book",
                    "number_of_cited_references",
                    "file_name",
                    "cited_by",
                    "author_count",
                    "citation_key",
                }
            )
            lowered[lowered_name if known_name else original_name] = value
        record.clear()
        record.update(lowered)
        for source, target in TABULAR_FIELD_ALIASES.items():
            if source in record and target not in record:
                record[target] = record.pop(source)
        if "id" in record:
            record["ID"] = record.pop("id")
        if "entrytype" in record:
            record["ENTRYTYPE"] = record.pop("entrytype")
        if "type" in record:
            record["ENTRYTYPE"] = record.pop("type")
        if "authors" in record:
            record["author"] = record.pop("authors")
        if "publication" in record:
            record["journal"] = record.pop("publication")
        record.pop("category", None)
        record.pop("affiliations", None)
        if "issue" in record and "number" not in record:
            record["number"] = record.pop("issue")
        if "publication_year" in record and "year" not in record:
            record["year"] = record.pop("publication_year")
        if "journal/book" in record and "journal" not in record and "doi" in record:
            record["journal"] = record.pop("journal/book")
        if "author" in record and isinstance(record["author"], str):
            record["author"] = record["author"].replace("; ", " and ")

        for key in list(record):
            value = record[key]
            if value in [f"no {key}", "", "nan"]:
                record.pop(key)
        if record.get("number") == "no issue":
            record.pop("number")
        if record.get("number_of_cited_references") == "no Number-of-Cited-References":
            record.pop("number_of_cited_references")
        if "no file" in record.get("file_name", ""):
            record.pop("file_name")
        if record.get("cited_by") == "no Times-Cited":
            record.pop("cited_by")
        record.pop("author_count", None)
        record.pop("citation_key", None)
        record.setdefault("ID", str(index).zfill(6))
        if "ENTRYTYPE" not in record:
            if record.get("journal", "") != "":
                record["ENTRYTYPE"] = "article"
            elif record.get("booktitle", "") != "":
                record["ENTRYTYPE"] = "inproceedings"
            else:
                record["ENTRYTYPE"] = "misc"
        if record["ENTRYTYPE"] == "inproceedings":
            if "journal" in record and "booktitle" not in record:
                record["booktitle"] = record.pop("journal")
        elif (
            record["ENTRYTYPE"] == "article"
            and "booktitle" in record
            and "journal" not in record
        ):
            record["journal"] = record.pop("booktitle")
        for key in list(record):
            value = record[key]
            if value is None or (isinstance(value, float) and isnan(value)):
                record.pop(key)
            else:
                record[key] = str(value)
    return records


def load_csv(
    text: str, *, normalize: bool = True
) -> list[dict[str, Any]] | dict[str, dict[str, Any]]:
    """Load CSV rows as bibliography records."""
    rows = list(csv.DictReader(StringIO(text)))
    if not normalize:
        return _records_from_un_normalized_list(rows)
    from .. import _normalize_without_source

    return _normalize_without_source(rows, format_name="csv")


def load_excel(source: Path, format: str) -> list[dict[str, Any]]:
    """Parse Excel rows into parser-level records using the optional Excel extra."""
    try:
        import pandas as pd

        rows = pd.read_excel(source).fillna("").to_dict(orient="records")
        return _records_from_un_normalized_list(rows)
    except ImportError as exc:
        raise OptionalBackendUnavailableError(
            f"Reading {format} files requires Excel dependencies. Install them with "
            "'pip install bibliography-io[excel]'."
        ) from exc
    except OptionalBackendUnavailableError:
        raise
    except Exception as exc:
        raise ParseError(f"Could not parse {format} file {source}: {exc}") from exc
