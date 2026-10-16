"""Tests for bibliography_io's standalone public API."""

import subprocess
import sys
from pathlib import Path

import bibliography_io as bibio
from bibliography_io import load_records
from bibliography_io import write_records


def test_strict_public_api_is_exposed() -> None:
    assert callable(bibio.loads)
    assert callable(bibio.dumps)
    assert callable(load_records)
    assert callable(write_records)


def test_package_import_does_not_require_optional_dependencies() -> None:
    source_path = Path(__file__).parents[1] / "src"
    script = """
import sys
sys.path.insert(0, sys.argv[1])
import bibliography_io
records = bibliography_io.loads("@article{sample, title={Standalone}}", format="bib")
assert records["sample"]["title"] == "Standalone"
"""
    subprocess.run(
        [sys.executable, "-S", "-c", script, str(source_path)],
        check=True,
        capture_output=True,
        text=True,
    )


def test_file_api_round_trip(tmp_path: Path) -> None:
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
    source = tmp_path / "input.bib"
    write_records(records, source)
    assert load_records(source) == records


def test_bibtex_and_ris_round_trip(tmp_path: Path) -> None:
    records = load_records(
        Path(__file__).parent / "data" / "bib" / "write_expected.bib"
    )

    bib_path = tmp_path / "roundtrip.bib"
    write_records(records, bib_path)
    assert load_records(bib_path) == records

    ris_path = tmp_path / "roundtrip.ris"
    write_records(records, ris_path)
    ris_records = load_records(ris_path)
    ris_record = next(iter(ris_records.values()))
    source_record = next(iter(records.values()))
    assert ris_record["title"] == source_record["title"]
    assert ris_record["author"] == source_record["author"]
    assert ris_record["doi"] == source_record["doi"]
