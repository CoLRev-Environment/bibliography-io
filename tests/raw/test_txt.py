"""Tests for EndNote TXT loading."""

import pytest

from bibliography_io import ParseError, loads_raw
from bibliography_io.loaders.txt import normalize_without_source


def test_txt_parser_preserves_tags_and_repeated_values() -> None:
    text = (
        "%0 Journal Article\n%T A title\n%A Ada\n%A Grace\n%8 2024\n\n%T Another title"
    )

    assert loads_raw(text, format="txt") == [
        {
            "0": "Journal Article",
            "T": "A title",
            "A": ["Ada", "Grace"],
            "8": "2024",
            "ENTRYTYPE": "article",
        },
        {"T": "Another title", "ENTRYTYPE": "article"},
    ]


def test_txt_mapping_keeps_its_own_reference_type_semantics() -> None:
    records = [
        {
            "0": "Journal Article",
            "T": "A title",
            "8": "2024",
            "ENTRYTYPE": "article",
        }
    ]

    assert normalize_without_source(records) == [
        {
            "ENTRYTYPE": "article",
            "type": "journal_article",
            "title": "A title",
            "date": "2024",
        }
    ]


@pytest.mark.parametrize(
    ("format", "text"),
    [("txt", "TI  - A title\n"), ("nbib", "%T A title\n")],
)
def test_nbib_and_txt_reject_the_other_formats_tag_syntax(
    format: str, text: str
) -> None:
    with pytest.raises(ParseError):
        loads_raw(text, format=format)
