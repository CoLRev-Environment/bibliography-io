"""Tests for normalized NBIB loading."""

from pathlib import Path

import pytest

import bibliography_io as bibio
from bibliography_io import load

DATA = Path(__file__).parents[1] / "data" / "nbib"


def test_load_nbib_fixture() -> None:
    with pytest.raises(bibio.MissingRecordIDError):
        load(DATA / "load.nbib")
