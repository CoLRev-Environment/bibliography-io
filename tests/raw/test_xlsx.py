"""Tests for Excel file APIs using the retained workbook fixture."""

from pathlib import Path

import pytest

from bibliography_io import load_raw, write


DATA = Path(__file__).parents[1] / "data" / "xlsx"
ORIGINAL_DUPLICATE_FIXTURE = DATA / "load.xlsx"


def test_xlsx_load_raw_preserves_source_columns() -> None:
    records = load_raw(ORIGINAL_DUPLICATE_FIXTURE)

    assert len(records) == 3
    assert records[0]["ID"] == "Id_0001"
    assert records[0]["Title"] == "Paper title"
    assert records[0]["type"] == "article"


def test_xlsx_load_write_round_trip(tmp_path: Path) -> None:
    records = {
        "one": {"ID": "one", "ENTRYTYPE": "article", "title": "One"},
        "two": {"ID": "two", "ENTRYTYPE": "article", "title": "Two"},
    }
    output = tmp_path / "roundtrip.xlsx"
    write(records, path=output)
    reloaded = load_raw(output)
    assert [row["title"] for row in reloaded] == ["One", "Two"]
    assert [row["ID"] for row in reloaded] == ["one", "two"]


def test_xlsx_writer_uses_legacy_layout_and_content_widths(tmp_path: Path) -> None:
    openpyxl = pytest.importorskip("openpyxl")
    records = {
        "z": {
            "ID": "z",
            "ENTRYTYPE": "article",
            "title": "x" * 135,
            "extra_z": "last",
            "extra_a": "",
            "empty": None,
        },
        "a": {
            "ID": "a",
            "ENTRYTYPE": "book",
            "title": "First",
            "extra_z": "first",
            "extra_a": "",
            "empty": "",
        },
    }
    output = tmp_path / "layout.xlsx"

    write(records, path=output)

    workbook = openpyxl.load_workbook(output)
    worksheet = workbook["Sheet1"]
    assert [cell.value for cell in worksheet[1]] == [
        "ID",
        "ENTRYTYPE",
        "title",
        "extra_z",
    ]
    assert [worksheet.cell(row=row, column=1).value for row in (2, 3)] == [
        "a",
        "z",
    ]
    assert worksheet.column_dimensions["C"].width == 130
    assert worksheet.column_dimensions["D"].width == 10


def test_xlsx_writer_can_preserve_input_field_and_record_order(
    tmp_path: Path,
) -> None:
    openpyxl = pytest.importorskip("openpyxl")
    records = {
        "z": {
            "ID": "z",
            "ENTRYTYPE": "article",
            "title": "Zulu",
            "zeta": "Z",
            "alpha": "A",
        },
        "a": {
            "ID": "a",
            "ENTRYTYPE": "article",
            "title": "Alpha",
            "alpha": "a",
            "zeta": "z",
        },
    }
    output = tmp_path / "input-order.xlsx"

    write(records, path=output, sort_fields=False, sort_by_id=False)

    worksheet = openpyxl.load_workbook(output)["Sheet1"]
    assert [cell.value for cell in worksheet[1]] == [
        "ID",
        "ENTRYTYPE",
        "title",
        "zeta",
        "alpha",
    ]
    assert [worksheet.cell(row=row, column=1).value for row in (2, 3)] == [
        "z",
        "a",
    ]
