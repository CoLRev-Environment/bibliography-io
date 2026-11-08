"""Optional Markdown reference-list loader."""

from __future__ import annotations

import logging
import os
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

from ..exceptions import BackendExecutionError, OptionalBackendUnavailableError
from ..normalization import _records_from_un_normalized_list

_GROBID_URL_ENV_VAR = "BIBLIOGRAPHY_IO_GROBID_URL"
_DEFAULT_GROBID_URL = "http://localhost:8070"


def normalize_without_source(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pass backend-normalized Markdown records to shared validation."""
    return records


def load_markdown(
    text: str, *, location: str | Path, normalize: bool = True
) -> list[dict[str, Any]] | dict[str, dict[str, Any]]:
    """Load reference-list Markdown through a plugin or the optional GROBID backend."""
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
                backend.loads(text, source=location)
                if hasattr(backend, "loads")
                else backend(text, source=location)
            )
            if isinstance(result, dict):
                result = list(result.values())
            records = _records_from_un_normalized_list(result)
            if normalize:
                from .. import _normalize_without_source

                return _normalize_without_source(records, format_name="md")
            return records
        except OptionalBackendUnavailableError:
            raise
        except Exception as exc:
            raise BackendExecutionError(
                "Markdown backend failed to parse references"
            ) from exc

    try:
        records = _load_with_grobid(text, location=location)
        if normalize:
            from .. import _normalize_without_source

            return _normalize_without_source(records, format_name="md")
        return records
    except OptionalBackendUnavailableError:
        raise
    except ImportError as exc:
        raise OptionalBackendUnavailableError(
            "Markdown reference-list parsing requires optional dependencies. "
            "Install them with 'pip install bibliography-io[markdown]'."
        ) from exc
    except Exception as exc:
        raise BackendExecutionError(
            "Markdown GROBID backend failed to parse references. Check that the "
            "GROBID service is running and reachable at "
            f"{os.environ.get(_GROBID_URL_ENV_VAR, _DEFAULT_GROBID_URL)!r}; "
            "bibliography-io does not start or manage the service."
        ) from exc


def _load_with_grobid(text: str, *, location: str | Path) -> list[dict[str, Any]]:
    try:
        from grobid_tei import GrobidClient, TEIDocument
    except ImportError as exc:
        raise OptionalBackendUnavailableError(
            "Markdown reference-list parsing requires optional dependencies. "
            "Install them with 'pip install bibliography-io[markdown]'."
        ) from exc

    logger = logging.getLogger(__name__)
    logger.info("Parsing Markdown references from %s", location)
    citations = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not citations:
        return []

    client = GrobidClient(
        service_url=os.environ.get(_GROBID_URL_ENV_VAR, _DEFAULT_GROBID_URL)
    )
    tei_xml = client.process_citation_list(citations, consolidate_citations=False)
    document = TEIDocument.from_bytes(tei_xml)

    records = []
    for index, reference in enumerate(document.references(), start=1):
        fields = dict(reference.fields)
        entrytype = fields.pop("entrytype", "misc")
        record = {"ID": str(index), "ENTRYTYPE": entrytype, **fields}
        records.append(record)
    return records
