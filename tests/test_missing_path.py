"""Tests for missing-path behavior in file loading APIs."""

from pathlib import Path

import pytest

from bibliography_io import load, load_primary, load_raw
from bibliography_io.exceptions import ParseError


def test_missing_path_opt_in_returns_empty_values(tmp_path: Path) -> None:
    missing = tmp_path / "not-created.json"

    assert load_raw(missing, missing_ok=True) == []
    assert load(missing, missing_ok=True) == {}


def test_missing_path_is_strict_by_default(tmp_path: Path) -> None:
    missing = tmp_path / "not-created.json"

    with pytest.raises(FileNotFoundError):
        load_raw(missing)
    with pytest.raises(FileNotFoundError):
        load(missing)


def test_missing_ok_does_not_suppress_non_file_paths(tmp_path: Path) -> None:
    directory = tmp_path / "existing.json"
    directory.mkdir()

    with pytest.raises(FileNotFoundError):
        load_raw(directory, missing_ok=True)
    with pytest.raises(FileNotFoundError):
        load(directory, missing_ok=True)


def test_missing_ok_does_not_suppress_parse_errors(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(ParseError):
        load_raw(malformed, missing_ok=True)
    with pytest.raises(ParseError):
        load(malformed, missing_ok=True)


def test_load_primary_keeps_missing_path_behavior(tmp_path: Path) -> None:
    assert load_primary(tmp_path / "not-created.bib") == {}
