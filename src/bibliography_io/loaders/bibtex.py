"""BibTeX bibliography loader."""

from __future__ import annotations

import re
from typing import Any

from ..exceptions import ParseError
from ..normalization import _records_from_loaded_list
from ..normalization import _records_from_un_normalized_list
from ..normalization import normalize_source_record

BIBTEX_FIELD_ALIASES = {
    "journaltitle": "journal",
    "shortjournal": "journal_abbreviation",
}


def _parse_fields(body: str) -> list[tuple[str, str]]:
    """Parse field assignments while allowing arbitrarily nested braces."""
    assignments = re.compile(r"([\w.-]+)\s*=\s*")
    fields = []
    position = 0
    while match := assignments.search(body, position):
        value_start = match.end()
        if value_start >= len(body):
            break
        if body[value_start] == "{":
            depth, escaped = 0, False
            value_end = value_start
            while value_end < len(body):
                char = body[value_end]
                if not escaped:
                    if char == "{":
                        depth += 1
                    elif char == "}":
                        depth -= 1
                        if depth == 0:
                            value_end += 1
                            break
                escaped = char == "\\" and not escaped
                if char != "\\":
                    escaped = False
                value_end += 1
            if depth:
                raise ParseError(
                    f"Unterminated braced BibTeX value for field {match.group(1)!r}"
                )
        elif body[value_start] == '"':
            escaped = False
            value_end = value_start + 1
            while value_end < len(body):
                char = body[value_end]
                if char == '"' and not escaped:
                    value_end += 1
                    break
                escaped = char == "\\" and not escaped
                if char != "\\":
                    escaped = False
                value_end += 1
            else:
                raise ParseError(
                    f"Unterminated quoted BibTeX value for field {match.group(1)!r}"
                )
        else:
            value_end = value_start
            while value_end < len(body) and body[value_end] not in ", \t\r\n":
                value_end += 1
        fields.append((match.group(1), body[value_start:value_end]))
        position = value_end
    return fields


def _decode_mapping(value: str, field: str) -> dict[str, dict[str, str]]:
    """Parse legacy provenance entries in ``field:source;note;`` form."""
    if not value.strip():
        return {}
    pattern = re.compile(r"([^:;\s]+):([^;]*);([^;]*);")
    result = {}
    consumed = []
    for match in pattern.finditer(value):
        name, source, note = match.groups()
        if name in result:
            raise ParseError(
                f"Duplicate provenance key {name!r} in BibTeX field {field!r}"
            )
        result[name] = {"source": source.strip(), "note": note.strip()}
        consumed.append((match.start(), match.end()))
    remainder = value
    for start, end in reversed(consumed):
        remainder = remainder[:start] + remainder[end:]
    if not result or remainder.strip():
        raise ParseError(f"Malformed provenance mapping in BibTeX field {field!r}")
    return result


def _decode_list(value: str, field: str) -> list[str]:
    """Parse semicolon-delimited BibTeX list values."""
    if not value.strip():
        return []
    if not value.rstrip().endswith(";"):
        raise ParseError(f"Malformed list in BibTeX field {field!r}")
    return [item.strip() for item in value.split(";") if item.strip()]


def load_bibtex(
    text: str,
    *,
    mapping_fields: frozenset[str] = frozenset(),
    list_fields: frozenset[str] = frozenset(),
    normalize: bool = True,
    header_only: bool = False,
) -> list[dict[str, Any]]:
    """Load BibTeX entries, optionally extracting only their headers."""
    parsed = []
    for entry in re.finditer(r"@([\w-]+)\s*[{(]\s*([^,\s]+)\s*,", text):
        start = entry.end()
        depth, brace, quoted, escaped, end = 1, 0, False, False, start
        opening = "{" if "{" in entry.group(0) else "("
        closing = "}" if opening == "{" else ")"
        while end < len(text):
            char = text[end]
            if char == '"' and not escaped and brace == 0:
                quoted = not quoted
            elif not quoted:
                if char == "{" and not escaped:
                    brace += 1
                elif char == "}" and not escaped and brace:
                    brace -= 1
                elif brace == 0 and char == closing and not escaped:
                    depth -= 1
                    if depth == 0:
                        break
                elif brace == 0 and char == "(" and not escaped:
                    depth += 1
                elif brace == 0 and char == ")" and closing == ")" and not escaped:
                    depth -= 1
                    if depth == 0:
                        break
            escaped = char == "\\" and not escaped
            if char != "\\":
                escaped = False
            end += 1
        record: dict[str, Any] = {
            "ID": entry.group(2),
            "ENTRYTYPE": entry.group(1).lower(),
        }
        if not header_only:
            body = text[start:end]
            for field_name, raw_value in _parse_fields(body):
                raw_value = raw_value.strip()
                value = raw_value
                if (value.startswith("{") and value.endswith("}")) or (
                    value.startswith('"') and value.endswith('"')
                ):
                    value = value[1:-1]
                field_name = field_name.lower()
                value = value.strip()
                if field_name in mapping_fields | list_fields:
                    if not raw_value.startswith("{"):
                        raise ParseError(
                            f"Structured BibTeX field {field_name!r} must use a braced value"
                        )
                    value = value.lstrip("{").rstrip("}")
                    record[field_name] = (
                        _decode_mapping(value, field_name)
                        if field_name in mapping_fields
                        else _decode_list(value, field_name)
                    )
                else:
                    record[field_name] = value
        parsed.append(
            normalize_source_record(
                record, format="bib", field_aliases=BIBTEX_FIELD_ALIASES
            )
            if normalize
            else record
        )
    if text.strip() and not parsed:
        raise ParseError("No BibTeX entries found")
    return (
        _records_from_loaded_list(parsed, format="bib")
        if normalize
        else _records_from_un_normalized_list(parsed)
    )
