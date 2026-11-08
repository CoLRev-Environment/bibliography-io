# Project guidance

## Python imports

- Keep imports from the same module on a single line when practical, including
  when importing multiple names.
- Use a parenthesized, multiline import only when a single imported name would
  make the import line too long.
- Do not expand a short import into a multiline list just to put each imported
  name on its own line. For example, prefer:

  ```python
  from .normalization import normalize_format
  from .normalization import normalize_records
  ```

  over a parenthesized multiline import.
- This preference applies to formatting only; preserve the project's existing
  import ordering and grouping conventions.
