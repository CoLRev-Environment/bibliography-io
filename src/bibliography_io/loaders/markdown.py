"""Optional Markdown reference-list loader."""

from __future__ import annotations

import logging
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

from ..exceptions import BackendExecutionError, OptionalBackendUnavailableError
from ..normalization import _records_from_un_normalized_list


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
            "Markdown GROBID backend failed to parse references"
        ) from exc


def _load_with_grobid(text: str, *, location: str | Path) -> list[dict[str, Any]]:
    import requests
    from colrev.env.grobid_service import GrobidService

    logger = logging.getLogger(__name__)
    logger.info("Parsing Markdown references from %s", location)
    grobid_service = GrobidService()
    grobid_service.check_grobid_availability()
    references = [line.rstrip() for line in text.splitlines() if "#" not in line[:2]]

    bibtex = ""
    for index, reference in enumerate(references, start=1):
        response = requests.post(
            grobid_service.GROBID_URL + "/api/processCitation",
            data={"consolidateCitations": "0", "citations": reference},
            headers={"Accept": "application/x-bibtex"},
            timeout=30,
        )
        bibtex += "\n" + response.text.replace("{-1,", "{" + str(index) + ",")

    from .bibtex import load_bibtex

    return load_bibtex(bibtex, normalize=False)
