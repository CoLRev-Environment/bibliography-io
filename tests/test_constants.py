"""Tests for package-owned constants and serialization semantics."""

import bibliography_io as bibio
from bibliography_io.constants import Colors
from bibliography_io.constants import ENTRYTYPES
from bibliography_io.constants import Fields


def test_generic_package_constants() -> None:
    assert Fields.ID == "ID"
    assert Fields.TITLE == "title"
    assert ENTRYTYPES.ARTICLE == "article"
    assert ENTRYTYPES.get_all()
    assert Fields.STATUS == "colrev_status"
    assert not hasattr(bibio.constants, "RecordState")
    assert not hasattr(ENTRYTYPES, "SEARCH")
    assert Colors.ORANGE == "\033[93m"
    assert Colors.END == "\033[0m"


def test_bibtex_metadata_remains_payload_data() -> None:
    records = bibio.loads("@article{sample, colrev_status={md_imported}}", format="bib")
    assert records[0][Fields.STATUS] == "md_imported"
    assert isinstance(records[0][Fields.STATUS], str)
