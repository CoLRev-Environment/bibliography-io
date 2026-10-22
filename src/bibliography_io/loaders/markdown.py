"""Optional Markdown reference-list loader."""

from __future__ import annotations

import logging
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

from ..exceptions import BackendExecutionError
from ..exceptions import OptionalBackendUnavailableError
from ..normalization import _records_from_loaded_list


def load_markdown(text: str, *, source: str | Path) -> list[dict[str, Any]]:
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
                backend.loads(text, source=source)
                if hasattr(backend, "loads")
                else backend(text, source=source)
            )
            if isinstance(result, dict):
                result = list(result.values())
            return _records_from_loaded_list(result)
        except OptionalBackendUnavailableError:
            raise
        except Exception as exc:
            raise BackendExecutionError(
                "Markdown backend failed to parse references"
            ) from exc

    try:
        return _load_with_grobid(text, source=source)
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


def _load_with_grobid(text: str, *, source: str | Path) -> list[dict[str, Any]]:
    import requests
    from colrev.env.grobid_service import GrobidService

    logger = logging.getLogger(__name__)
    logger.info("Parsing Markdown references from %s", source)
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

    return load_bibtex(bibtex)
