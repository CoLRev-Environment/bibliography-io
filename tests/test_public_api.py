"""Tests for the package's public API."""

import logging
from pathlib import Path

import bibliography_io as bibio
from bibliography_io import load_records
from bibliography_io import write_records


def test_public_api_aliases() -> None:
    """The concise API names directly alias the implementation functions."""
    assert callable(load_records)
    assert callable(write_records)
    assert bibio.load is load_records
    assert bibio.write is write_records
    assert bibio.write_file is write_records


def test_both_api_patterns_are_equivalent(tmp_path: Path) -> None:
    """Both public API styles accept the existing keyword arguments."""
    logger = logging.getLogger(__name__)
    source = tmp_path / "input.bib"
    records = {
        "example2024": {
            "ID": "example2024",
            "ENTRYTYPE": "article",
            "author": "Example, Alex",
            "journal": "Example Journal",
            "title": "An Example",
            "year": "2024",
        }
    }

    write_records(records, filename=source)
    explicitly_loaded = load_records(filename=source, logger=logger)
    namespace_loaded = bibio.load(filename=source, logger=logger)

    assert explicitly_loaded == namespace_loaded == records

    explicit_output = tmp_path / "explicit.bib"
    namespace_output = tmp_path / "namespace.bib"
    write_records(explicitly_loaded, filename=explicit_output)
    bibio.write(namespace_loaded, filename=namespace_output)
    assert explicit_output.read_text(encoding="utf-8") == namespace_output.read_text(
        encoding="utf-8"
    )


def test_bibtex_and_ris_round_trip(tmp_path: Path) -> None:
    """The root API can write and reload BibTeX and RIS records."""
    records = {
        "10.1234/EXAMPLE": {
            "ID": "10.1234/EXAMPLE",
            "ENTRYTYPE": "article",
            "author": "Example, Alex",
            "doi": "10.1234/EXAMPLE",
            "journal": "Example Journal",
            "pages": "10--20",
            "title": "An Example",
            "year": "2024",
        }
    }

    bib_path = tmp_path / "roundtrip.bib"
    write_records(records, filename=bib_path)
    assert load_records(filename=bib_path) == records

    ris_path = tmp_path / "roundtrip.ris"
    bibio.write(records, filename=ris_path)
    ris_records = bibio.load(filename=ris_path, unique_id_field="DO")
    assert ris_records == records
