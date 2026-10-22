"""Optional Markdown reference-list parsing through CoLRev and GROBID."""

from __future__ import annotations

import logging
from pathlib import Path
from tempfile import TemporaryDirectory


def loads(text: str, *, source: str | Path) -> list[dict]:
    """Parse reference lines with the legacy CoLRev/GROBID loader."""
    from .loader.md import MarkdownLoader

    logger = logging.getLogger(__name__)
    logger.info("Parsing Markdown references from %s", source)
    with TemporaryDirectory(prefix="bibliography-io-markdown-") as directory:
        filename = Path(directory) / "references.md"
        filename.write_text(text, encoding="utf-8")
        loader = MarkdownLoader(filename=filename, logger=logger)
        return loader.load_records_list()
