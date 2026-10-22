"""BibTeX bibliography loader."""

from __future__ import annotations

import base64
import json
import re
from typing import Any

from ..exceptions import ParseError
from ..normalization import _records_from_loaded_list
from ..normalization import normalize_source_record

_STRUCTURED_BIB_PREFIX = "bibio-json-v1:"
BIBTEX_FIELD_ALIASES = {
    "journaltitle": "journal",
    "shortjournal": "journal_abbreviation",
}


def _decode_structured_value(value: str, field: str) -> Any:
    if not value.startswith(_STRUCTURED_BIB_PREFIX):
        raise ParseError(
            f"BibTeX field {field!r} is declared structured but does not use "
            f"the {_STRUCTURED_BIB_PREFIX!r} encoding"
        )
    try:
        payload = base64.b64decode(value[len(_STRUCTURED_BIB_PREFIX) :], validate=True)
        result = json.loads(payload.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ParseError(
            f"Malformed structured value in BibTeX field {field!r}"
        ) from exc
    if not isinstance(result, (dict, list)):
        raise ParseError(
            f"Structured BibTeX field {field!r} must decode to a mapping or list"
        )
    return result


def load_bibtex(
    text: str,
    *,
    mapping_fields: frozenset[str] = frozenset(),
    list_fields: frozenset[str] = frozenset(),
) -> list[dict[str, Any]]:
    """Load BibTeX entries, including explicitly declared structured fields."""
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
                if char == "{":
                    brace += 1
                elif char == "}" and brace:
                    brace -= 1
                elif brace == 0 and char == closing:
                    depth -= 1
                    if depth == 0:
                        break
                elif brace == 0 and char == "(":
                    depth += 1
                elif brace == 0 and char == ")" and closing == ")":
                    depth -= 1
                    if depth == 0:
                        break
            escaped = char == "\\" and not escaped
            if char != "\\":
                escaped = False
            end += 1
        body = text[start:end]
        record: dict[str, Any] = {
            "ID": entry.group(2),
            "ENTRYTYPE": entry.group(1).lower(),
        }
        for field in re.finditer(
            r'([\w-]+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|"(?:[^"]|\\.)*"|[^,\s]+)\s*,?',
            body,
            re.DOTALL,
        ):
            raw_value = field.group(2).strip()
            value = raw_value
            if (value.startswith("{") and value.endswith("}")) or (
                value.startswith('"') and value.endswith('"')
            ):
                value = value[1:-1]
            field_name = field.group(1).lower()
            value = value.strip()
            if field_name in mapping_fields | list_fields:
                if not raw_value.startswith("{"):
                    raise ParseError(
                        f"Structured BibTeX field {field_name!r} must use a braced value"
                    )
                value = value.lstrip("{").rstrip("}")
                prefix_index = value.find(_STRUCTURED_BIB_PREFIX)
                if prefix_index >= 0:
                    value = value[prefix_index:]
                decoded = _decode_structured_value(value, field_name)
                expected_type = dict if field_name in mapping_fields else list
                expected_label = "mapping" if expected_type is dict else "list"
                if not isinstance(decoded, expected_type):
                    raise ParseError(
                        f"Structured BibTeX field {field_name!r} was declared as a "
                        f"{expected_label} field but does not decode to a {expected_label}"
                    )
                record[field_name] = decoded
            else:
                record[field_name] = value
        parsed.append(
            normalize_source_record(
                record, format="bib", field_aliases=BIBTEX_FIELD_ALIASES
            )
        )
    if text.strip() and not parsed:
        raise ParseError("No BibTeX entries found")
    return _records_from_loaded_list(parsed)
