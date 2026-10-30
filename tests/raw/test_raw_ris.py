"""Tests for RIS loading and writing against repository fixtures."""

import json
from pathlib import Path

import pytest

from bibliography_io import load_raw
from bibliography_io import loads_raw
from bibliography_io import write
from bibliography_io.loaders.ris import load_ris
from bibliography_io.writers.ris import write_ris


DATA = Path(__file__).parents[1] / "data" / "ris"


def test_load_ris_fixtures() -> None:
    raw_expected = json.loads(
        (DATA / "load_raw_expected.json").read_text(encoding="utf-8")
    )
    raw_records = load_raw(DATA / "load.ris")

    assert raw_records == raw_expected


def test_ris_new_type_tag_closes_unterminated_record() -> None:
    text = "TY  - JOUR\nTI  - First\nTY  - JOUR\nTI  - Second\nER  -"

    records = loads_raw(text, format="ris")

    assert len(records) == 2
    assert [record["TI"] for record in records] == ["First", "Second"]


def test_ris_type_tag_is_preserved_in_raw_mode(tmp_path: Path) -> None:
    text = "TY  - CONF\nID  - conf-one\nTI  - Conference paper\nER  -"
    source = tmp_path / "conference.ris"
    source.write_text(text, encoding="utf-8")

    raw = load_raw(source)

    assert raw == [{"TY": "CONF", "ID": "conf-one", "TI": "Conference paper"}]
    assert "ENTRYTYPE" not in raw[0]


def test_load_ris_type_tag_raw_mode() -> None:
    assert load_ris("TY  - CONF\nTI  - Conference paper\nER  -", normalize=False) == [
        {"TY": "CONF", "TI": "Conference paper"}
    ]


def test_ris_write_file_matches_expected_fixture(tmp_path: Path) -> None:
    records = load_raw(DATA / "write_expected.bib")
    output = tmp_path / "written.ris"
    write(records, path=output)
    assert loads_raw(output.read_text(encoding="utf-8"), format="ris") == load_raw(
        DATA / "write_expected.ris"
    )


def test_ris_writer_uses_legacy_order_and_field_mappings() -> None:
    records = {
        "z-record": {
            "ID": "z-record",
            "ENTRYTYPE": "article",
            "title": "Second",
            "author": "Last, First and Other, Author",
            "year": "2020",
            "pages": "12--19",
            "journal": "Journal",
            "volume": "3",
            "number": "2",
            "abstract": "Abstract",
            "url": "https://example.test",
            "doi": "10.1234/example",
            "issn": "1111-2222",
            "isbn": "978-1-2345-6789-0",
            "publisher": "Unsupported",
        },
        "a-record": {
            "ID": "a-record",
            "ENTRYTYPE": "phdthesis",
            "title": "First",
            "year": "UNKNOWN",
        },
    }

    with pytest.warns(UserWarning, match="unsupported RIS field 'publisher'"):
        text = write_ris(records)

    assert text == (
        "TY  - THES\nTI  - First\nID  - a-record\nER  -\n\n"
        "TY  - JOUR\nTI  - Second\nAU  - Last, First\nAU  - Other, Author\n"
        "PY  - 2020\nSP  - 12\nEP  - 19\nJO  - Journal\nVL  - 3\n"
        "IS  - 2\nN2  - Abstract\nUR  - https://example.test\n"
        "SN  - 1111-2222\nSN  - 978-1-2345-6789-0\nDO  - 10.1234/example\n"
        "ID  - z-record\nER  -"
    )


def test_ris_writer_warns_for_each_skipped_field_in_each_record() -> None:
    records = {
        "first": {"ID": "first", "ENTRYTYPE": "misc", "publisher": "One"},
        "second": {
            "ID": "second",
            "ENTRYTYPE": "misc",
            "publisher": "Two",
            "keywords": ["keyword"],
        },
    }

    with pytest.warns(UserWarning) as captured:
        write_ris(records)

    assert len(captured) == 3
    assert [str(warning.message) for warning in captured] == [
        "Skipping unsupported RIS field 'publisher' in record 'first'",
        "Skipping unsupported RIS field 'publisher' in record 'second'",
        "Skipping unsupported RIS field 'keywords' in record 'second'",
    ]
