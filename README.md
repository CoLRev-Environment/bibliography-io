<div align="center">

# bibliography-io

[![PyPI - Version](https://img.shields.io/pypi/v/bibliography-io?color=blue)](https://pypi.org/project/bibliography-io/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/bibliography-io)
[![License](https://img.shields.io/github/license/CoLRev-Environment/bibliography-io)](https://github.com/CoLRev-Environment/bibliography-io/blob/main/LICENSE)
[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/CoLRev-Environment/bibliography-io/ci.yml?label=tests)](https://github.com/CoLRev-Environment/bibliography-io/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/github/actions/workflow/status/CoLRev-Environment/bibliography-io/docs.yml?label=docs)](https://github.com/CoLRev-Environment/bibliography-io/actions/workflows/docs.yml)

</div>

`bibliography-io` provides standalone loading and writing of bibliographic
records. Its core API does not require CoLRev or GROBID.

## Installation

Install the base package with:

```shell
pip install bibliography-io
```

The optional `colrev` extra is for legacy compatibility modules. It is not
needed by the core file and string APIs. Markdown reference-list parsing has no
released optional backend yet.

## Usage

```python
from bibliography_io import load_records, write_records

records = load_records("references.bib")
write_records(records, "references.ris")
```

File APIs infer the format from recognized suffixes; an explicit `format` can
override inference. String APIs always require `format`:

```python
from bibliography_io import dumps, loads

records = loads("@article{example, title={An example}}", format="bib")
text = dumps(records, format="bib")
```

### Format support

| Format | Read files | Write files | String APIs |
| --- | --- | --- | --- |
| BibTeX | Yes | Yes | `loads` / `dumps` |
| RIS | Yes | Yes | `loads` / `dumps` |
| CSV | Yes | Yes | `loads` / `dumps` |
| Excel | `.xls`, `.xlsx` | `.xlsx` | File APIs only |
| ENL / EndNote | `.enl`, `.txt` | No | `loads` only |
| NBIB | Yes | No | `loads` only |
| JSON | Yes | No | `loads` only |
| Markdown table | No | Yes | `dumps` |
| Markdown reference list | Pending optional backend | No | Pending optional backend |

Markdown table serialization is built into the core. Markdown reference-list
parsing is a separate optional feature; its backend and installation extra are
not finalized. Requesting Markdown input without a registered backend raises
``OptionalBackendUnavailableError``.

Historical root aliases (``load``, ``write``, ``write_file``, ``to_string``,
``load_df``, and ``get_nr_records``) are deprecated immediately and will be
removed in a future release.

See the [documentation](https://colrev-environment.github.io/bibliography-io/)
for installation details, usage examples, and the generated API reference.

## Development

Install the package's core test extra and run the standalone core suite. The
``--confcutdir`` option avoids loading legacy root fixtures, which import
CoLRev:

```shell
pip install -e ".[test]"
pip install build pre-commit
pre-commit install
pre-commit run --all-files
pytest --confcutdir=tests/core_api tests/core_api
```

Build the documentation locally with:

```shell
pip install -e ".[docs]"
python -m sphinx -W --keep-going -b html docs docs/_build/html
```

See [RELEASING.md](RELEASING.md) for the package build and publication process.

## License

This project is distributed under the [MIT License](LICENSE).
