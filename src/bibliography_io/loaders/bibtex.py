"""BibTeX bibliography loader."""

from __future__ import annotations

import re
from typing import Any
import itertools
import os
import string

import typing
from pathlib import Path
import logging

from ..constants import Fields
from ..exceptions import ParseError
from ..normalization import _records_from_un_normalized_list
from ..normalization import normalize_source_record

BIBTEX_FIELD_ALIASES = {
    "journaltitle": "journal",
    "shortjournal": "journal_abbreviation",
}


def normalize_without_source(
    records: list[dict[str, Any]],
    *,
    mapping_fields: frozenset[str] = frozenset(),
    list_fields: frozenset[str] = frozenset(),
) -> list[dict[str, Any]]:
    """Normalize standard BibTeX fields while preserving unknown field names."""
    for index, record in enumerate(records):
        records[index] = normalize_source_record(
            record,
            format="bib",
            field_aliases=BIBTEX_FIELD_ALIASES,
            generic_normalization=True,
        )
        record = records[index]
        record.setdefault("ENTRYTYPE", "misc")
        record["ENTRYTYPE"] = str(record["ENTRYTYPE"]).lower()
        if record["ENTRYTYPE"] in {"www", "electronic"}:
            record["ENTRYTYPE"] = "misc"
    return records


_HEADER_FIELDS = frozenset(
    {
        Fields.ORIGIN,
        Fields.STATUS,
        Fields.FILE,
        Fields.SCREENING_CRITERIA,
        Fields.MD_PROV,
    }
)


def _parse_fields(
    body: str, *, field_filter: frozenset[str] | None = None
) -> list[tuple[str, str]]:
    """Parse field assignments while allowing arbitrarily nested braces."""
    assignments = re.compile(r"([\w.-]+)\s*=\s*")
    parsed_fields = []
    position = 0
    while match := assignments.search(body, position):
        include_field = field_filter is None or match.group(1).lower() in field_filter
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
            if depth and include_field:
                raise ParseError(
                    f"Unterminated braced BibTeX value for field {match.group(1)!r}"
                )
            if depth:
                value_end = len(body)
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
                if include_field:
                    raise ParseError(
                        f"Unterminated quoted BibTeX value for field {match.group(1)!r}"
                    )
                value_end = len(body)
        else:
            value_end = value_start
            while value_end < len(body) and body[value_end] not in ", \t\r\n":
                value_end += 1
        if include_field:
            parsed_fields.append((match.group(1), body[value_start:value_end]))
        position = value_end
    return parsed_fields


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
) -> list[dict[str, Any]] | dict[str, dict[str, Any]]:
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
        body = text[start:end]
        header_fields = _HEADER_FIELDS if header_only else None
        for field_name, raw_value in _parse_fields(body, field_filter=header_fields):
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
        parsed.append(record)
    if text.strip() and not parsed:
        raise ParseError("No BibTeX entries found")
    if normalize:
        from .. import _normalize_without_source

        return _normalize_without_source(
            parsed,
            format_name="bib",
            mapping_fields=mapping_fields,
            list_fields=list_fields,
        )
    return _records_from_un_normalized_list(parsed)


def run_resolve_crossref(records: dict, *, logger: logging.Logger) -> None:
    """Resolve cross-references between records."""
    # Handle cross-references between records
    crossref_ids = []
    for record_dict in records.values():
        if "crossref" not in record_dict:
            continue

        crossref_record = records.get(record_dict["crossref"], None)

        if not crossref_record:
            logger.error(f"crossref record (ID={record_dict['crossref']}) not found")
            continue
        crossref_ids.append(crossref_record["ID"])
        for key, value in crossref_record.items():
            if key not in record_dict:
                record_dict[key] = value
        del record_dict["crossref"]

    for crossref_id in dict.fromkeys(crossref_ids):
        del records[crossref_id]


def run_fix_bib_file(filename: Path, *, logger: logging.Logger) -> None:
    """Repair malformed BibTeX entries by modifying the file in place.

    Scan the file line by line and apply the following corrections:
    - Replace semicolons in citation keys with underscores.
    - Resolve duplicate citation keys by appending alphabetic suffixes
    (a, b, ..., z, aa, ab, ...).
    - Replace whitespace between two words in citation keys with underscores.
    - Replace whitespace between two words in field names with underscores.

    Corrections are applied directly to the original file without creating
    a backup. The function uses line-based pattern matching rather than
    parsing BibTeX and therefore handles only specific malformed patterns.

    Args:
        filename: Path to the BibTeX file to repair.
        logger: Logger used to report corrections.
    """
    # pylint: disable=too-many-statements

    def fix_key(
        file: typing.IO, line: bytes, replacement_line: bytes, seekpos: int
    ) -> int:
        logger.info(
            f"Fix invalid key: \n{line.decode('utf-8')}"
            f"{replacement_line.decode('utf-8')}"
        )
        line = file.readline()
        remaining = line + file.read()
        file.seek(seekpos)
        file.write(replacement_line)
        seekpos = file.tell()
        file.flush()
        os.fsync(file)
        file.write(remaining)
        file.truncate()  # if the replacement is shorter...
        file.seek(seekpos)
        return seekpos

    def generate_next_unique_id(
        *,
        temp_id: str,
        existing_ids: list,
    ) -> str:
        """Get the next unique ID."""
        order = 0
        letters = list(string.ascii_lowercase)
        next_unique_id = temp_id
        appends: list = []
        while next_unique_id.lower() in [i.lower() for i in existing_ids]:
            if len(appends) == 0:
                order += 1
                appends = list(itertools.product(letters, repeat=order))
            next_unique_id = temp_id + "".join(list(appends.pop(0)))
        temp_id = next_unique_id
        return temp_id

    if filename is not None:
        with open(filename, encoding="utf8") as bibtex_file:
            contents = bibtex_file.read()
            if len(contents) < 10:
                return

        # Errors to fix before pybtex loading:
        # - set_incremental_ids (otherwise, not all records will be loaded)
        # - fix_keys (keys containing white spaces)
        record_ids: typing.List[str] = []
        with open(filename, "r+b") as file:
            seekpos = file.tell()
            line = file.readline()
            while line:
                if b"@" in line[:3]:
                    current_id = line[line.find(b"{") + 1 : line.rfind(b",")]
                    current_id_str = current_id.decode("utf-8").lstrip().rstrip()

                    if any(x in current_id_str for x in [";"]):
                        replacement_line = re.sub(
                            r";",
                            r"_",
                            line.decode("utf-8"),
                        ).encode("utf-8")
                        seekpos = fix_key(file, line, replacement_line, seekpos)

                    if current_id_str in record_ids:
                        next_id = generate_next_unique_id(
                            temp_id=current_id_str, existing_ids=record_ids
                        )
                        logger.info(f"Fix duplicate ID: {current_id_str} >> {next_id}")

                        replacement_line = (
                            line.decode("utf-8")
                            .replace(current_id.decode("utf-8"), next_id)
                            .encode("utf-8")
                        )

                        line = file.readline()
                        remaining = line + file.read()
                        file.seek(seekpos)
                        file.write(replacement_line)
                        seekpos = file.tell()
                        file.flush()
                        os.fsync(file)
                        file.write(remaining)
                        file.truncate()  # if the replacement is shorter...
                        file.seek(seekpos)

                        record_ids.append(next_id)

                    else:
                        record_ids.append(current_id_str)

                # Fix keys
                if re.match(
                    r"^\s*[a-zA-Z0-9]+\s+[a-zA-Z0-9]+\s*\=", line.decode("utf-8")
                ):
                    replacement_line = re.sub(
                        r"(^\s*)([a-zA-Z0-9]+)\s+([a-zA-Z0-9]+)(\s*\=)",
                        r"\1\2_\3\4",
                        line.decode("utf-8"),
                    ).encode("utf-8")
                    seekpos = fix_key(file, line, replacement_line, seekpos)

                # Fix IDs
                if re.match(
                    r"^@[a-zA-Z0-9]+\{[a-zA-Z0-9]+\s[a-zA-Z0-9]+,",
                    line.decode("utf-8"),
                ):
                    replacement_line = re.sub(
                        r"^(@[a-zA-Z0-9]+\{[a-zA-Z0-9]+)\s([a-zA-Z0-9]+,)",
                        r"\1_\2",
                        line.decode("utf-8"),
                    ).encode("utf-8")
                    seekpos = fix_key(file, line, replacement_line, seekpos)

                seekpos = file.tell()
                line = file.readline()
