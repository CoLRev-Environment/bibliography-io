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

## Usage

```python
from bibliography_io import load_records, write_records

records = load_records("references.bib")
write_records(records, "references.ris")
```

File formats are inferred from suffixes. String operations require an explicit
format:

```python
from bibliography_io import dumps, loads

records = loads("@article{example, title={An example}}", format="bib")
text = dumps(records, format="bib")
```

Core operation requires no CoLRev installation. Markdown table writing is
included; Markdown reference-list parsing requires an optional backend.
Historical root aliases (`load`, `write`, `write_file`, `to_string`, `load_df`,
and `get_nr_records`) are deprecated immediately and will be removed in a
future release.

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
