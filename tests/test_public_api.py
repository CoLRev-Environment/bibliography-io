"""Tests for bibliography_io's standalone public API."""

import subprocess
import sys
from inspect import signature
from pathlib import Path

import pytest

import bibliography_io as bibio
from bibliography_io import load_raw, write


def test_strict_public_api_is_exposed() -> None:
    assert callable(bibio.loads_raw)
    assert callable(bibio.loads)
    assert callable(bibio.to_string)
    assert callable(load_raw)
    assert callable(write)
    assert callable(bibio.load_primary)
    assert callable(bibio.loads_primary)
    assert callable(bibio.load_df)
    assert callable(bibio.load_primary_df)
    assert callable(bibio.get_nr_records)
    assert "normalize" not in signature(bibio.load_raw).parameters
    assert "normalize" not in signature(bibio.loads_raw).parameters
    assert "normalize" not in signature(bibio.load).parameters
    assert "format" in signature(bibio.load).parameters
    assert "format" in signature(bibio.load_df).parameters
    assert not hasattr(bibio, "load_raw_df")


def test_package_import_does_not_require_optional_dependencies() -> None:
    source_path = Path(__file__).parents[1] / "src"
    script = """
import sys
sys.path.insert(0, sys.argv[1])
import bibliography_io
records = bibliography_io.loads_raw(
    "@article{sample, title={Standalone}}", format="bib"
)
assert records[0]["title"] == "Standalone"
"""
    subprocess.run(
        [sys.executable, "-S", "-c", script, str(source_path)],
        check=True,
        capture_output=True,
        text=True,
    )


def test_raw_and_generic_load_contracts(tmp_path: Path) -> None:
    source = tmp_path / "records.ris"
    source.write_text("TY  - JOUR\nTI  - A title\nAU  - Ada\nER  -", encoding="utf-8")

    assert bibio.load_raw(source) == [{"TY": "JOUR", "TI": "A title", "AU": "Ada"}]
    assert bibio.load(source) == [
        {
            "ENTRYTYPE": "article",
            "ID": "000001",
            "title": "A title",
            "author": "Ada",
        }
    ]


def test_load_format_can_override_suffix(tmp_path: Path) -> None:
    source = tmp_path / "references.txt"
    source.write_text("TY  - JOUR\nTI  - A title\nER  -", encoding="utf-8")

    assert bibio.load(source, format="ris") == [
        {"ENTRYTYPE": "article", "ID": "000001", "title": "A title"}
    ]


def test_loads_generic_text_contract() -> None:
    assert bibio.loads("TY  - JOUR\nTI  - A title\nAU  - Ada\nER  -", format="ris") == [
        {
            "ENTRYTYPE": "article",
            "ID": "000001",
            "title": "A title",
            "author": "Ada",
        }
    ]


def test_txt_uses_generic_normalization() -> None:
    assert bibio.loads("%T A tagged title\n", format="txt") == [
        {"ENTRYTYPE": "article", "title": "A tagged title"}
    ]


def test_load_normalizes_json_field_values_to_strings(tmp_path: Path) -> None:
    source = tmp_path / "records.json"
    source.write_text(
        '[{"ENTRYTYPE":"ARTICLE","ID":7,"Title":42,'
        '"authors":["Ada","Grace"],"metadata":{"rank":2}}]',
        encoding="utf-8",
    )

    record = bibio.load(source)[0]

    assert record == {
        "ENTRYTYPE": "article",
        "ID": "7",
        "title": "42",
        "author": "Ada and Grace",
        "metadata": "{'rank': 2}",
    }
    assert all(isinstance(value, str) for value in record.values())


def test_loads_rejects_excel_formats() -> None:
    for format_name in ("xls", "xlsx"):
        with pytest.raises(bibio.UnsupportedFormatError, match="from text"):
            bibio.loads("not an excel file", format=format_name)


def test_load_df_forwards_format_override(tmp_path: Path) -> None:
    pytest.importorskip("pandas")
    source = tmp_path / "references.txt"
    source.write_text("TY  - JOUR\nTI  - A title\nER  -", encoding="utf-8")

    records = bibio.load_df(source, format="ris")

    assert records.loc[0, "ENTRYTYPE"] == "article"
    assert records.loc[0, "title"] == "A title"


def test_load_df_delegates_to_load_with_source_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("pandas")
    calls: list[tuple[str | None, str | None, str | None]] = []

    def fake_load(
        path: str | Path,
        *,
        source: str | None,
        source_version: str | None,
        format: str | None,
    ) -> list[dict[str, object]]:
        calls.append((source, source_version, format))
        return [{"ID": "one", "title": "Title"}]

    monkeypatch.setattr(bibio, "load", fake_load)

    records = bibio.load_df(
        "references.data",
        source="colrev.crossref",
        source_version="2026",
        format="ris",
    )

    assert calls == [("colrev.crossref", "2026", "ris")]
    assert records.loc[0, "title"] == "Title"


def test_source_plugin_load_pipeline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "records.ris"
    source.write_text("TY  - JOUR\nTI  - A title\nER  -", encoding="utf-8")
    calls: list[tuple[str, str, str | None]] = []

    class Plugin:
        endpoint = "colrev.provider_x"

        @classmethod
        def preprocess(
            cls, text: str, *, format: str, source_version: str | None
        ) -> str:
            calls.append(("preprocess", format, source_version))
            return text.replace("A title", "Prepared title")

        @classmethod
        def normalize(
            cls,
            records: list[dict[str, object]],
            *,
            format: str,
            source_version: str | None,
        ) -> dict[str, dict[str, object]]:
            calls.append(("normalize", format, source_version))
            record = {
                "ID": "provider-id",
                "ENTRYTYPE": "ARTICLE",
                "title": records[0]["TI"],
                "count": 3,
                "authors": ["Ada", "Grace"],
                "metadata": {"rank": 2},
                "custom-field": "kept",
            }
            return {"provider-id": record}

    class Point:
        name = "search_source"

        @staticmethod
        def load() -> type[Plugin]:
            return Plugin

    class Points:
        @staticmethod
        def select(*, group: str, name: str) -> list[Point]:
            assert group == "colrev"
            assert name == "search_source"
            return [Point()]

    monkeypatch.setattr(bibio, "entry_points", lambda: Points())

    records = bibio.load(source, source="colrev.provider_x", source_version="2026")

    expected_source_record = {
        "ID": "provider-id",
        "ENTRYTYPE": "article",
        "title": "Prepared title",
        "count": "3",
        "authors": "Ada; Grace",
        "metadata": "{'rank': 2}",
        "custom-field": "kept",
    }
    assert records == [expected_source_record]
    assert all(isinstance(value, str) for value in records[0].values())
    string_records = bibio.loads(
        "TY  - JOUR\nTI  - A title\nER  -",
        format="ris",
        source="colrev.provider_x",
        source_version="2026",
    )
    assert string_records == [expected_source_record]
    assert calls == [
        ("preprocess", "ris", "2026"),
        ("normalize", "ris", "2026"),
        ("preprocess", "ris", "2026"),
        ("normalize", "ris", "2026"),
    ]


def test_missing_source_plugin_raises_optional_backend_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "records.bib"
    source.write_text("@article{one, title={Title}}", encoding="utf-8")

    class Points:
        @staticmethod
        def select(*, group: str, name: str) -> list[object]:
            assert group == "colrev"
            assert name == "search_source"
            return []

    monkeypatch.setattr(bibio, "entry_points", lambda: Points())

    with pytest.raises(
        bibio.OptionalBackendUnavailableError, match="colrev.provider_x"
    ):
        bibio.load(source, source="colrev.provider_x")


def test_duplicate_source_endpoints_raise_backend_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "records.bib"
    source.write_text("@article{one, title={Title}}", encoding="utf-8")

    class Plugin:
        endpoint = "colrev.provider_x"

    class Point:
        name = "search_source"

        @staticmethod
        def load() -> type[Plugin]:
            return Plugin

    class Points:
        @staticmethod
        def select(*, group: str, name: str) -> list[Point]:
            assert group == "colrev"
            assert name == "search_source"
            return [Point(), Point()]

    monkeypatch.setattr(bibio, "entry_points", lambda: Points())

    with pytest.raises(bibio.BackendExecutionError, match="Multiple CoLRev"):
        bibio.load(source, source="colrev.provider_x")


def test_dataframe_apis_report_missing_optional_extra() -> None:
    source_path = Path(__file__).parents[1] / "src"
    script = """
import sys
import tempfile
sys.path.insert(0, sys.argv[1])
from pathlib import Path
import bibliography_io
from bibliography_io.exceptions import OptionalBackendUnavailableError
with tempfile.TemporaryDirectory() as directory:
    source = Path(directory) / "records.bib"
    source.write_text("@article{one, title={One}}", encoding="utf-8")
    for loader in (
        bibliography_io.load_df,
        bibliography_io.load_primary_df,
    ):
        try:
            loader(source)
        except OptionalBackendUnavailableError as exc:
            assert "[excel]" in str(exc)
        else:
            raise AssertionError("pandas extra should be required")
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
import sys
import tempfile
sys.path.insert(0, sys.argv[1])
from pathlib import Path
from bibliography_io import write
from bibliography_io.exceptions import OptionalBackendUnavailableError
with tempfile.TemporaryDirectory() as directory:
    try:
        write(
            {"one": {"ID": "one", "ENTRYTYPE": "article"}},
            path=Path(directory) / "out.xlsx",
        )
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
    write(records, path=source)
    assert load_raw(source) == list(records.values())


def test_serializers_sort_list_records_by_id_by_default(tmp_path: Path) -> None:
    records = [
        {"ID": "z-last", "ENTRYTYPE": "article", "title": "Last"},
        {"ID": "a-first", "ENTRYTYPE": "article", "title": "First"},
    ]
    original = [record.copy() for record in records]

    text = bibio.to_string(records, format="bib")
    string_output = bibio.write_string(records, "bib")
    output = tmp_path / "sorted.bib"
    write(records, path=output)

    assert [record["ID"] for record in bibio.loads_raw(text, format="bib")] == [
        "a-first",
        "z-last",
    ]
    assert [
        record["ID"] for record in bibio.loads_raw(string_output, format="bib")
    ] == ["a-first", "z-last"]
    assert [record["ID"] for record in load_raw(output)] == ["a-first", "z-last"]
    assert records == original


def test_serializers_can_preserve_list_input_order(tmp_path: Path) -> None:
    records = [
        {"ID": "z-last", "ENTRYTYPE": "article", "title": "Last"},
        {"ID": "a-first", "ENTRYTYPE": "article", "title": "First"},
    ]

    text = bibio.to_string(records, format="bib", sort_by_id=False)
    string_output = bibio.write_string(records, "bib", sort_by_id=False)
    output = tmp_path / "input-order.bib"
    write(records, path=output, sort_by_id=False)

    assert [record["ID"] for record in bibio.loads_raw(text, format="bib")] == [
        "z-last",
        "a-first",
    ]
    assert [
        record["ID"] for record in bibio.loads_raw(string_output, format="bib")
    ] == ["z-last", "a-first"]
    assert [record["ID"] for record in load_raw(output)] == ["z-last", "a-first"]


@pytest.mark.parametrize("sort_by_id", [True, False])
def test_mapping_input_always_preserves_insertion_order(
    tmp_path: Path, sort_by_id: bool
) -> None:
    records = {
        "z-last": {"ID": "z-last", "ENTRYTYPE": "article", "title": "Last"},
        "a-first": {"ID": "a-first", "ENTRYTYPE": "article", "title": "First"},
    }

    text = bibio.to_string(records, format="bib", sort_by_id=sort_by_id)
    string_output = bibio.write_string(records, "bib", sort_by_id=sort_by_id)
    output = tmp_path / f"mapping-{sort_by_id}.bib"
    write(records, path=output, sort_by_id=sort_by_id)

    expected_ids = ["a-first", "z-last"] if sort_by_id else ["z-last", "a-first"]
    assert [record["ID"] for record in bibio.loads_raw(text, format="bib")] == (
        expected_ids
    )
    assert [
        record["ID"] for record in bibio.loads_raw(string_output, format="bib")
    ] == expected_ids
    assert [record["ID"] for record in load_raw(output)] == expected_ids


def test_missing_file_helpers_return_empty_results(tmp_path: Path) -> None:
    missing = tmp_path / "missing.bib"

    assert bibio.get_nr_records(missing) == 0


def test_removed_compatibility_aliases_are_not_exposed() -> None:
    for name in ("write_file", "load_raw_df", "dumps"):
        assert not hasattr(bibio, name)


def test_write_requires_keyword_path(tmp_path: Path) -> None:
    records = {"example": {"ID": "example", "ENTRYTYPE": "article"}}
    output = tmp_path / "example.bib"

    write(records, path=output)
    assert output.is_file()

    try:
        write(records, output)
    except TypeError:
        pass
    else:
        raise AssertionError("write must reject a positional path")


def test_bibtex_and_ris_round_trip(tmp_path: Path) -> None:
    records = load_raw(Path(__file__).parent / "data" / "bib" / "write_expected.bib")

    bib_path = tmp_path / "roundtrip.bib"
    write(records, path=bib_path)
    assert load_raw(bib_path) == records

    ris_path = tmp_path / "roundtrip.ris"
    write(records, path=ris_path)
    ris_records = bibio.load(ris_path)
    ris_record = next(iter(ris_records))
    source_record = next(iter(records))
    assert ris_record["title"] == source_record["title"]
    assert ris_record["author"] == source_record["author"]
    assert ris_record["doi"] == source_record["doi"]
