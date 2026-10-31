"""Tests for normalized Excel loading."""

from pathlib import Path

import pytest

import bibliography_io as bibio
from bibliography_io import load

DATA = Path(__file__).parents[1] / "data" / "xlsx"
ORIGINAL_DUPLICATE_FIXTURE = DATA / "load.xlsx"


def test_load_xlsx_fixture() -> None:
    with pytest.raises(bibio.DuplicateRecordIDError, match="Id_0001"):
        load(ORIGINAL_DUPLICATE_FIXTURE)


def test_load_xlsx_generic_normalization_preserves_explicit_id(
    tmp_path: Path,
) -> None:
    pytest.importorskip("pandas")
    openpyxl = pytest.importorskip("openpyxl")
    source = tmp_path / "records.xlsx"
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.append(["ID", "ENTRYTYPE", "title", "year"])
    worksheet.append(["spreadsheet-1", "article", "A title", 2023])
    workbook.save(source)

    records = load(source)

    assert records == {
        "spreadsheet-1": {
            "ID": "spreadsheet-1",
            "ENTRYTYPE": "article",
            "title": "A title",
            "year": "2023",
        }
    }


def test_xlsx_source_normalization_uses_parsed_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("pandas")
    calls: list[tuple[str, str | None, int]] = []
    processed_paths: list[Path] = []
    file_hook_calls: list[tuple[Path, str, str | None, Path]] = []

    class SearchSource:
        endpoint = "colrev.test_xlsx"

        @classmethod
        def preprocess(
            cls, text: str, *, format: str, source_version: str | None
        ) -> str:
            raise AssertionError("binary Excel input must not be preprocessed as text")

        @classmethod
        def preprocess_file(
            cls,
            path: Path,
            *,
            format: str,
            source_version: str | None,
            output_dir: Path,
        ) -> Path:
            import pandas as pd

            file_hook_calls.append((path, format, source_version, output_dir))
            processed_path = output_dir / path.name
            frame = pd.read_excel(path)
            frame["Title"] = "Preprocessed title"
            frame.to_excel(processed_path, index=False)
            processed_paths.append(processed_path)
            return processed_path

        @classmethod
        def normalize(
            cls,
            records: list[dict[str, object]],
            *,
            format: str,
            source_version: str | None,
        ) -> dict[str, dict[str, object]]:
            calls.append((format, source_version, len(records)))
            return {
                str(index): {"ID": str(index), "title": record["Title"]}
                for index, record in enumerate(records, start=1)
            }

    class EntryPoint:
        @staticmethod
        def load() -> type[SearchSource]:
            return SearchSource

    class EntryPoints:
        @staticmethod
        def select(*, group: str, name: str) -> list[EntryPoint]:
            assert group == "colrev"
            assert name == "search_source"
            return [EntryPoint()]

    monkeypatch.setattr(bibio, "entry_points", lambda: EntryPoints())

    records = load(
        ORIGINAL_DUPLICATE_FIXTURE,
        source="colrev.test_xlsx",
        source_version="2026",
    )

    assert len(records) == 3
    assert records["1"]["title"] == "Preprocessed title"
    assert calls == [("xlsx", "2026", 3)]
    assert file_hook_calls == [
        (ORIGINAL_DUPLICATE_FIXTURE, "xlsx", "2026", processed_paths[0].parent)
    ]
    assert len(processed_paths) == 1
    assert not processed_paths[0].exists()
    assert ORIGINAL_DUPLICATE_FIXTURE.is_file()


def test_xlsx_file_hook_failure_cleans_up_temporary_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    partial_paths: list[Path] = []

    class SearchSource:
        endpoint = "colrev.test_xlsx"

        @classmethod
        def preprocess_file(
            cls,
            path: Path,
            *,
            format: str,
            source_version: str | None,
            output_dir: Path,
        ) -> Path:
            partial_path = output_dir / path.name
            partial_path.write_bytes(path.read_bytes())
            partial_paths.append(partial_path)
            raise RuntimeError("preprocessing failed")

    class EntryPoint:
        @staticmethod
        def load() -> type[SearchSource]:
            return SearchSource

    class EntryPoints:
        @staticmethod
        def select(*, group: str, name: str) -> list[EntryPoint]:
            assert group == "colrev"
            assert name == "search_source"
            return [EntryPoint()]

    monkeypatch.setattr(bibio, "entry_points", lambda: EntryPoints())

    with pytest.raises(bibio.BackendExecutionError, match="preprocess xlsx file"):
        load(ORIGINAL_DUPLICATE_FIXTURE, source="colrev.test_xlsx")

    assert len(partial_paths) == 1
    assert not partial_paths[0].exists()
    assert ORIGINAL_DUPLICATE_FIXTURE.is_file()
