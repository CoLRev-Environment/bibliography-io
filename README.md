# bibliography-io

`bibliography-io` loads and writes bibliographic records in formats including
BibTeX, RIS, CSV, Excel, Markdown, ENL, NBIB, and JSON.

## Installation

Install the base package with:

```shell
pip install bibliography-io
```

The load and write functions use CoLRev's shared metadata definitions. Install
the `colrev` extra to use them:

```shell
pip install "bibliography-io[colrev]"
```

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

## Development

Install the project with its optional runtime dependencies and development
tools, then run the hooks and test suite:

```shell
pip install -e ".[all]"
pip install build pre-commit pytest pytest-mock twine
pre-commit install
pre-commit run --all-files
pytest tests/test_public_api.py
```

See [RELEASING.md](RELEASING.md) for the package build and publication process.
