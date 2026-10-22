<div align="center">

<img src="docs/_static/bibliography_io_logo.png" alt="bibliography-io logo" width="400">

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

Install optional features as needed:

```shell
pip install "bibliography-io[markdown]"  # Markdown parsing through CoLRev/GROBID
pip install "bibliography-io[excel]"     # Excel file support
pip install "bibliography-io[all]"       # Both optional features
```

Markdown reference-list parsing also requires a running GROBID service. Core
formats do not require either extra.

## Usage

```python
from bibliography_io import load_records, write_records

records = load_records("references.bib")
write_records(records, path="references.ris")
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
| BibTeX (`.bib`) | Yes | Yes | `loads` / `dumps` |
| RIS (`.ris`) | Yes | Yes | `loads` / `dumps` |
| ENL / EndNote (`.enl`) | Yes | *Planned* | `loads` (`dumps` planned) |
| NBIB (`.nbib`) | Yes | *Planned* | `loads` (`dumps` planned) |
| JSON (`.json`) | Yes | *Planned* | `loads` (`dumps` planned) |
| CSV (`.csv`) | Yes | Yes | `loads` / `dumps` |
| Excel (`.xls`, `.xlsx`) | Yes | Yes | File APIs only |
| Markdown (`.md`) | *Planned* | *Planned* | *Planned* |

Markdown table serialization is built into the core.
Markdown reference-list parsing is planned as a separate optional feature; its
backend and installation extra are not finalized. Requesting Markdown
reference-list input without a registered backend raises
``OptionalBackendUnavailableError``.

See the [documentation](https://colrev-environment.github.io/bibliography-io/)
for installation details, usage examples, and the generated API reference.

## Development

See the [development documentation](https://colrev-environment.github.io/bibliography-io/development.html)
for test, lint, and documentation build instructions.

## Related Python Libraries

The following libraries support additional bibliographic formats, conversion workflows, and reference extraction:

- [**rispy**](https://github.com/MrTango/rispy) — A lightweight Python library for reading and writing RIS files. Supports configurable tag mappings and custom parsers/writers. Best suited for standalone RIS processing.
- [**pybtexris**](https://pypi.org/project/pybtexris/) — A Pybtex plugin for reading RIS files and converting them into formats such as BibTeX. Also supports bibliography formatting through Pybtex.
- [**pybtexnbib**](https://pypi.org/project/pybtexnbib/) — A Pybtex plugin for parsing PubMed/MEDLINE (`.nbib`) files. Useful for integrating PubMed references into BibTeX and other bibliography workflows.
- [**endnote-utils**](https://pypi.org/project/endnote-utils/) — A utility for converting EndNote XML and RIS records to CSV, JSON, and Excel formats. Also provides command-line tools for bibliographic data processing.
- [**Biopython (Bio.Medline)**](https://biopython.org/) — Provides parsers for MEDLINE-formatted records, including PubMed exports. Best suited for biomedical literature processing.
- [**pubmed-parser**](https://github.com/titipata/pubmed_parser) — A Python library for extracting structured metadata from PubMed and PubMed Central XML datasets. Particularly useful for large-scale biomedical literature analysis.

## License

This project is distributed under the [MIT License](LICENSE).
