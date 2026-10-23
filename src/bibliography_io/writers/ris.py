"""RIS bibliography writer."""

from __future__ import annotations

from typing import Any

from ..loaders.ris import RIS_MAP


def write_ris(records: dict[str, dict[str, Any]]) -> str:
    """Write normalized records as RIS."""
    reverse = {value: key for key, value in RIS_MAP.items()}
    lines = []
    for record in records.values():
        typ = {
            "article": "JOUR",
            "inproceedings": "CONF",
            "book": "BOOK",
            "inbook": "CHAP",
        }.get(record["ENTRYTYPE"], "GEN")
        lines.append(f"TY  - {typ}")
        for key, value in record.items():
            if key in {"ID", "ENTRYTYPE"}:
                continue
            values = value if isinstance(value, list) else [value]
            tag = reverse.get(key, key.upper()[:2])
            lines.extend(f"{tag}  - {item}" for item in values)
        lines.extend([f"ID  - {record['ID']}", "ER  - ", ""])
    return "\n".join(lines).rstrip()
