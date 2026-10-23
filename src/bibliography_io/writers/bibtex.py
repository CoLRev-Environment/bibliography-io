"""BibTeX bibliography writer."""

from __future__ import annotations

from typing import Any

from ..exceptions import SerializationError
from ..normalization import normalize_field_name

_FIELD_NAME_WIDTH = len("colrev_masterdata_provenance")

_DEFAULT_FIELD_ORDER = (
    "colrev_origin",
    "colrev_status",
    "colrev_masterdata_provenance",
    "colrev_data_provenance",
    "colrev_pdf_id",
    "screening_criteria",
    "file",
    "prescreen_exclusion",
    "doi",
    "grobid-version",
    "colrev.dblp.dblp_key",
    "colrev.semantic_scholar.id",
    "colrev.web_of_science.unique-id",
    "author",
    "booktitle",
    "journal",
    "title",
    "year",
    "volume",
    "number",
    "pages",
    "editor",
    "publisher",
    "url",
    "abstract",
)


def _brace_scalar(value: Any) -> str:
    if isinstance(value, (dict, list, tuple, set)):
        raise SerializationError(f"Cannot write non-scalar BibTeX value: {value!r}")
    text = str(value)
    depth, escaped = 0, False
    for char in text:
        if not escaped:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth < 0:
                    raise SerializationError(
                        f"Cannot write BibTeX value with unbalanced braces: {value!r}"
                    )
        escaped = char == "\\" and not escaped
        if char != "\\":
            escaped = False
    if depth:
        raise SerializationError(
            f"Cannot write BibTeX value with unbalanced braces: {value!r}"
        )
    return "{" + text + "}"


def _validate_delimited_text(value: Any, *, field: str) -> str:
    if not isinstance(value, str):
        raise SerializationError(
            f"BibTeX structured field {field!r} must contain only strings"
        )
    if any(char in value for char in ";{}\n\r"):
        raise SerializationError(
            f"BibTeX structured field {field!r} values contain reserved delimiters"
        )
    return value


def _encode_mapping(value: dict[str, Any], field: str) -> list[str]:
    """Serialize provenance as ``field:source;note;`` entries."""
    entries = []
    for name, provenance in value.items():
        if (
            not isinstance(name, str)
            or not name
            or any(char in name for char in ":;{}")
            or any(char.isspace() for char in name)
        ):
            raise SerializationError(
                f"BibTeX provenance field {field!r} has an invalid key: {name!r}"
            )
        if not isinstance(provenance, dict):
            raise SerializationError(
                f"BibTeX provenance field {field!r} values must be mappings"
            )
        if set(provenance) - {"source", "note"}:
            raise SerializationError(
                f"BibTeX provenance field {field!r} supports only 'source' and 'note'"
            )
        source = _validate_delimited_text(provenance.get("source"), field=field)
        note = _validate_delimited_text(provenance.get("note", ""), field=field)
        entries.append(f"{name}:{source};{note};")
    return entries


def _encode_list(value: list[Any], field: str) -> list[str]:
    """Serialize list items using the semicolon-delimited BibTeX convention."""
    return [f"{_validate_delimited_text(item, field=field)};" for item in value]


def _braced_lines(prefix: str, values: list[str]) -> str:
    if not values:
        return "{}"
    continuation = " " * (len(prefix) + 1)
    return "{" + ("\n" + continuation).join(values) + "}"


def write_bibtex(
    records: dict[str, dict[str, Any]],
    *,
    mapping_fields: frozenset[str] = frozenset(),
    list_fields: frozenset[str] = frozenset(),
    field_order: tuple[str, ...] | None = None,
    sort_fields: bool = True,
) -> str:
    """Write normalized records as BibTeX."""
    preferred_fields = (
        field_order
        if field_order is not None
        else tuple(
            normalize_field_name(field, preserve_dots=True)
            for field in _DEFAULT_FIELD_ORDER
        )
    )
    field_positions = {field: index for index, field in enumerate(preferred_fields)}
    entries = []
    for record in records.values():
        fields = []
        ordered_fields = record.items()
        if sort_fields:
            ordered_fields = sorted(
                ordered_fields,
                key=lambda item: (
                    field_positions.get(
                        normalize_field_name(item[0], preserve_dots=True),
                        len(field_positions),
                    ),
                    normalize_field_name(item[0], preserve_dots=True),
                ),
            )
        for key, value in ordered_fields:
            if key in {"ID", "ENTRYTYPE"}:
                continue
            field_name = key.lower()
            if field_name in mapping_fields | list_fields:
                expected_type = dict if field_name in mapping_fields else list
                expected_label = "mapping" if expected_type is dict else "list"
                if not isinstance(value, expected_type):
                    raise SerializationError(
                        f"BibTeX field {key!r} was declared as a {expected_label} "
                        f"field but has value {value!r}"
                    )
                prefix = f"   {key:<{_FIELD_NAME_WIDTH}}  = "
                values = (
                    _encode_mapping(value, key)
                    if expected_type is dict
                    else _encode_list(value, key)
                )
                value = _braced_lines(prefix, values)
            else:
                value = _brace_scalar(value)
            fields.append(f"   {key:<{_FIELD_NAME_WIDTH}}  = {value}")
        if fields:
            fields[-1] += ","
        entries.append(
            f"@{record['ENTRYTYPE']}{{{record['ID']},\n" + ",\n".join(fields) + "\n}"
        )
    return "\n\n".join(entries)
