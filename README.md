# bibliography-io

`bibliography-io` loads and writes bibliographic records in formats including
BibTeX, RIS, CSV, Excel, Markdown, ENL, NBIB, and JSON.

## Explicit function imports

```python
from bibliography_io import load_records, write_records

records = load_records(filename="references.bib")
write_records(records, filename="references.ris")
```

`load_records` accepts the same options as the loader's `load()` function;
`write_records` accepts the same options as the writer's `write_file()` function.

## Namespace imports

For a shorter namespace-style interface, `load` and `write` are aliases of the
same functions:

```python
import bibliography_io as bibio

records = bibio.load(filename="references.bib")
bibio.write(records, filename="references.ris")
```

Both patterns share the same implementations and preserve the loader and writer
options, return values, and supported formats.
