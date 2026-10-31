<div align="center">

<img src="https://raw.githubusercontent.com/CoLRev-Environment/bibliography-io/main/docs/_static/bibliography_io_logo.png" alt="bibliography-io logo" width="400">

# bibliography-io

[![PyPI - Version](https://img.shields.io/pypi/v/bibliography-io?color=blue)](https://pypi.org/project/bibliography-io/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/bibliography-io)
[![License](https://img.shields.io/github/license/CoLRev-Environment/bibliography-io)](https://github.com/CoLRev-Environment/bibliography-io/blob/main/LICENSE)
[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/CoLRev-Environment/bibliography-io/ci.yml?label=tests)](https://github.com/CoLRev-Environment/bibliography-io/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/github/actions/workflow/status/CoLRev-Environment/bibliography-io/docs.yml?label=docs)](https://github.com/CoLRev-Environment/bibliography-io/actions/workflows/docs.yml)

</div>

`bibliography-io` addresses the distinct requirements of bibliographic data management throughout literature reviews: robust ingestion of heterogeneous source data and efficient, reproducible management of primary records.

These stages have different priorities:

- **Ingestion and normalization adapt source data for processing.** `load()` orchestrates parsing and normalization, applying source-specific rules to transform differing source structures into a common primary record representation.
- **Primary data management prioritizes efficiency and reproducibility.** Normalized records follow a consistent schema with unique IDs. Frequent reading and writing require efficient dictionary-based access, partial header loading, targeted updates, and deterministic serialization that avoids meaningless Git diffs.

Accordingly, `bibliography-io` distinguishes two interfaces:

- **`load()`** — Orchestrated ingestion and normalization that parses source-specific structures into a common primary record representation.
- **`load_primary()`** — Efficient I/O for consistently structured primary records.

Unlike format-specific libraries with differing internal representations, `bibliography-io` provides a common record structure across input formats, enabling source-independent processing in subsequent literature review steps.

The package also minimizes dependencies, requiring specialized packages (e.g., for Excel or GROBID-based extraction) only when needed, facilitating integration into diverse literature review workflows.

<!--
**Guiding principle:** Forgiving at the boundaries, strict in the core, and reproducible by design.
-->

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

Markdown reference-list parsing also requires a running GROBID service. Formats
available in the base bibliography-io installation do not require either extra.

## Usage

```python
from bibliography_io import load, load_primary, write

records = load("references.bib", source="colrev.web_of_science")
write(records, path="primary.bib", primary=True)
primary_records = load_primary("primary.bib")
```

File APIs infer the format from recognized suffixes; an explicit `format` can
override inference. String APIs always require `format`:

```python
from bibliography_io import to_string
from bibliography_io import loads_raw

records = loads_raw("@article{example, title={An example}}", format="bib")
text = to_string(records, format="bib")
```

File formats are inferred from their suffixes; pass `format` to `load()` when a
suffix is ambiguous or does not match the file's actual format.

### Format support

| Format | Read files | Write files | String APIs |
| --- | --- | --- | --- |
| BibTeX (`.bib`) | Yes | Yes | `loads_raw()` / `to_string()` |
| RIS (`.ris`) | Yes | Yes | `loads_raw()` / `to_string()` |
| ENL / EndNote (`.enl`) | Yes | *Planned* | `loads_raw()` (`to_string()` planned) |
| NBIB (`.nbib`) | Yes | *Planned* | `loads_raw()` (`to_string()` planned) |
| JSON (`.json`) | Yes | *Planned* | `loads_raw()` (`to_string()` planned) |
| CSV (`.csv`) | Yes | Yes | `loads_raw()` / `to_string()` |
| Excel (`.xls`, `.xlsx`) | Yes | Yes | File APIs only |
| Markdown (`.md`) | *Planned* | *Planned* | *Planned* |

Markdown table writing is built into bibliography-io.
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

- [**BibtexParser**](https://github.com/sciunto-org/python-bibtexparser) — A lightweight, actively maintained library for reading, writing, and modifying `.bib` files. Supports customizable parsing, field transformations, and BibTeX writing. Best suited for general-purpose BibTeX processing.
- [**Pybtex**](https://pybtex.org/) — A bibliography processing library that supports BibTeX parsing, citation formatting, and conversion between bibliography formats. Provides extensible formatting styles and output formats such as LaTeX, HTML, and plain text. Best suited for generating formatted references.
- [**biblib**](https://pypi.org/project/biblib/) — A library for managing bibliographic databases, including merging entries, accessing metadata, and retrieving references using DOI or ISBN identifiers. Useful for building custom bibliography management workflows, although its last PyPI release was in 2018.
- [**rispy**](https://github.com/MrTango/rispy) — A lightweight Python library for reading and writing RIS files. Supports configurable tag mappings and custom parsers/writers. Best suited for standalone RIS processing.
- [**pybtexris**](https://pypi.org/project/pybtexris/) — A Pybtex plugin for reading RIS files and converting them into formats such as BibTeX. Also supports bibliography formatting through Pybtex.
- [**pybtexnbib**](https://pypi.org/project/pybtexnbib/) — A Pybtex plugin for parsing PubMed/MEDLINE (`.nbib`) files. Useful for integrating PubMed references into BibTeX and other bibliography workflows.
- [**endnote-utils**](https://pypi.org/project/endnote-utils/) — A utility for converting EndNote XML and RIS records to CSV, JSON, and Excel formats. Also provides command-line tools for bibliographic data processing.
- [**Biopython (Bio.Medline)**](https://biopython.org/) — Provides parsers for MEDLINE-formatted records, including PubMed exports. Best suited for biomedical literature processing.
- [**pubmed-parser**](https://github.com/titipata/pubmed_parser) — A Python library for extracting structured metadata from PubMed and PubMed Central XML datasets. Particularly useful for large-scale biomedical literature analysis.

## License

This project is distributed under the [MIT License](LICENSE).
