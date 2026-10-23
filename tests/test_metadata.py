"""Tests for bibliography metadata writing semantics."""

import bibliography_io as bibio


def test_bibtex_metadata_remains_payload_data() -> None:
    records = bibio.loads_raw(
        "@article{sample, colrev_status={md_imported}}", format="bib"
    )
    assert records[0]["colrev_status"] == "md_imported"
    assert isinstance(records[0]["colrev_status"], str)
