"""Tests for bibliography_io's standalone public API."""

import subprocess
import sys
from pathlib import Path

import pytest

import bibliography_io as bibio
from bibliography_io import load
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
assert records[0]["title"] == "Standalone"
"""
    subprocess.run(
        [sys.executable, "-S", "-c", script, str(source_path)],
        check=True,
        capture_output=True,
        text=True,
    )


def test_excel_write_reports_missing_optional_extra() -> None:
    source_path = Path(__file__).parents[1] / "src"
    script = """
import sys, tempfile
sys.path.insert(0, sys.argv[1])
from pathlib import Path
from bibliography_io import write_records
from bibliography_io.exceptions import OptionalBackendUnavailableError
with tempfile.TemporaryDirectory() as directory:
    try:
        write_records({"one": {"ID": "one", "ENTRYTYPE": "article"}},
                      path=Path(directory) / "out.xlsx")
    except OptionalBackendUnavailableError as exc:
        assert "[excel]" in str(exc)
    else:
        raise AssertionError("Excel extra should be required")
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
    write_records(records, path=source)
    assert load_records(source) == list(records.values())


def test_write_records_requires_keyword_path(tmp_path: Path) -> None:
    records = {"example": {"ID": "example", "ENTRYTYPE": "article"}}
    output = tmp_path / "example.bib"

    write_records(records, path=output)
    assert output.is_file()

    try:
        write_records(records, output)
    except TypeError:
        pass
    else:
        raise AssertionError("write_records must reject a positional path")


def test_deprecated_load_alias_delegates_to_core_api(tmp_path: Path) -> None:
    source = tmp_path / "input.bib"
    source.write_text("@article{example, title={Example}}", encoding="utf-8")

    with pytest.warns(DeprecationWarning):
        records = load(source)

    assert records[0]["title"] == "Example"


def test_deprecated_load_alias_rejects_legacy_colrev_options(
    tmp_path: Path,
) -> None:
    with (
        pytest.warns(DeprecationWarning),
        pytest.raises(TypeError, match="CoLRev-specific load options"),
    ):
        load(tmp_path / "input.bib", entrytype_setter=lambda record: None)


def test_bibtex_and_ris_round_trip(tmp_path: Path) -> None:
    records = load_records(
        Path(__file__).parent / "data" / "bib" / "write_expected.bib"
    )

    bib_path = tmp_path / "roundtrip.bib"
    write_records(records, path=bib_path)
    assert load_records(bib_path) == records

    ris_path = tmp_path / "roundtrip.ris"
    write_records(records, path=ris_path)
    ris_records = load_records(ris_path)
    ris_record = next(iter(ris_records))
    source_record = next(iter(records))
    assert ris_record["title"] == source_record["title"]
    assert ris_record["author"] == source_record["author"]
    assert ris_record["doi"] == source_record["doi"]
