"""Shared fixtures for tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest


class Helpers:
    """Helpers for retrieving test data files."""

    test_data_path = Path(__file__).parent

    @staticmethod
    def retrieve_test_file(*, source: Path, target: Path) -> None:
        """Copy a test data file to a target path."""
        target.parent.mkdir(exist_ok=True, parents=True)
        shutil.copy(Helpers.test_data_path / source, target)

    @staticmethod
    def retrieve_test_file_content(*, source: Path) -> str:
        """Read a test data file as UTF-8 text."""
        return (Helpers.test_data_path / source).read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def helpers() -> type[Helpers]:
    """Return helpers for accessing test data."""
    return Helpers
