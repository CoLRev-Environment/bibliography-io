<div align="center">

# bibliography-io

[![PyPI - Version](https://img.shields.io/pypi/v/bibliography-io?color=blue)](https://pypi.org/project/bibliography-io/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/bibliography-io)
[![License](https://img.shields.io/github/license/CoLRev-Environment/bibliography-io)](https://github.com/CoLRev-Environment/bibliography-io/blob/main/LICENSE)
[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/CoLRev-Environment/bibliography-io/ci.yml?label=tests)](https://github.com/CoLRev-Environment/bibliography-io/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/github/actions/workflow/status/CoLRev-Environment/bibliography-io/docs.yml?label=docs)](https://github.com/CoLRev-Environment/bibliography-io/actions/workflows/docs.yml)

</div>

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

## Usage

```python
from bibliography_io import load_records, write_records

records = load_records(filename="references.bib")
write_records(records, filename="references.ris")
```

`load_records` accepts the same options as the loader's `load()` function;
`write_records` accepts the same options as the writer's `write_file()` function.

For a shorter namespace-style interface, `load` and `write` are aliases of the
same functions:

```python
import bibliography_io as bibio

records = bibio.load(filename="references.bib")
bibio.write(records, filename="references.ris")
```

Both patterns share the same implementations and preserve the loader and writer
options, return values, and supported formats.

See the [documentation](https://colrev-environment.github.io/bibliography-io/)
for installation details, usage examples, and the generated API reference.

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

Build the documentation locally with:

```shell
pip install -e ".[docs]"
python -m sphinx -W --keep-going -b html docs docs/_build/html
```

See [RELEASING.md](RELEASING.md) for the package build and publication process.

## License

This project is distributed under the [MIT License](LICENSE).
