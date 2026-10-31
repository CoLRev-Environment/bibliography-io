Usage
=====

File and string APIs
--------------------

File APIs accept a path as ``str`` or ``pathlib.Path``. They infer the format
from a recognized suffix, unless ``format`` is supplied explicitly. Reads use
UTF-8 and missing files raise ``FileNotFoundError``.

.. code-block:: python

   from pathlib import Path

    from bibliography_io import load_raw, write

    records = load_raw(Path("references.bib"))
    write(records, path="references.ris")

String APIs require an explicit ``format``:

.. code-block:: python

    from bibliography_io import to_string
    from bibliography_io import loads_raw

    records = loads_raw("@article{example, title={An example}}", format="bib")
    bibtex = to_string(records, format="bib")

Supported formats
-----------------

``load_raw`` reads BibTeX (``.bib``), RIS (``.ris``), CSV (``.csv``),
Excel (``.xls`` and ``.xlsx``), ENL/EndNote (``.enl`` and ``.txt``), NBIB
(``.nbib``), and JSON (``.json``). It also accepts Markdown (``.md``) for
reference-list parsing only when the optional backend is installed.

``write`` writes BibTeX, RIS, CSV, Excel (``.xlsx``), and Markdown
tables. JSON, ENL, NBIB, and legacy Excel (``.xls``) are read-only. ``to_string``
supports BibTeX, RIS, CSV, and Markdown-table output. Excel is a file-only
format; ``loads_raw`` supports the string-based input formats.

Use ``write(..., primary=True)`` to write a primary-record mapping. This mode
validates that records have unique, non-empty IDs and valid entry types, and
only permits BibTeX output.

Serialization sorts records by their record IDs by default for both list and
mapping inputs. Set ``sort_by_id=False`` on ``write()``, ``to_string()``, or
``write_string()`` to preserve list order or mapping iteration order. The
``primary=True`` mode of ``write()`` continues to sort primary records by ID.

Format aliases include ``bibtex`` for BibTeX, ``excel`` for Excel, ``endnote``
for ENL, and ``markdown`` for Markdown. File suffixes are case-insensitive.

Markdown forms and optional dependencies
-----------------------------------------

Markdown table output is built into bibliography-io and does not need an
optional backend. Markdown reference-list parsing uses CoLRev and GROBID and is
enabled by installing ``bibliography-io[markdown]``. A running GROBID service is
also required. Without the extra, a Markdown read raises
``OptionalBackendUnavailableError``. Excel loading and writing require
``bibliography-io[excel]``; the ``all`` extra installs both optional feature
sets.

.. _record-shape:

Record shape
------------

``load_raw()`` and ``loads_raw()`` return records in source order as a list of
dictionaries. They preserve parser-level field names and value types: values
may be strings, lists for repeated fields, mappings, or other format-native
values. Raw loading does not require or generate record IDs, and it does not
apply source-specific normalization. Unknown fields are retained.

``load()`` and ``loads()`` return a dictionary keyed by record ID, with
normalized field names and string values. IDs must be non-empty strings and
unique; missing or duplicate IDs raise ``MissingRecordIDError`` or
``DuplicateRecordIDError``. The ID-indexed mapping supports processing imported
records as primary records, including merging and processing them, while
retaining IDs for back-tracing records to their imports. This applies both to
generic normalization and to results returned by source-specific normalization
hooks. Repeated values are combined into strings (authors use `` and ``;
keywords use ``; ``; other conflicting values use ``; ``). Empty scalar values
and empty items in repeated values are omitted. A source-specific hook may select
and normalize fields, but its non-string field values are converted to strings
before ``load()`` or ``loads()`` returns. Supply a ``source`` identifier and
optional ``source_version`` to use source-specific preprocessing and
normalization:

.. code-block:: python

    from bibliography_io import load

    records = load(
        "references.ris",
        source="colrev.crossref",
        source_version="2026",
    )

Without ``source``, ``load()`` applies bibliography-io's generic normalization.
When a source is selected, ``source`` names the CoLRev package by its unique
endpoint identifier, such as ``colrev.crossref``. The format is inferred from
the file suffix unless ``format`` is supplied; use ``format`` if the suffix is
ambiguous or does not match the file's actual format. See
:doc:`source_extensions` for package discovery and preprocessing/normalization
hook details.

DataFrame helpers
-----------------

``load_df()`` returns the normalized records from ``load()`` as DataFrame rows
in source order, with record IDs as the index. It accepts ``source``,
``source_version``, and ``format``. ``load_primary_df()`` returns primary
records with IDs as the DataFrame index. Parser-level records remain available
as lists through ``load_raw()`` and ``loads_raw()``. Pandas is optional; install
the Excel extra with ``pip install bibliography-io[excel]`` to use these helpers.

``get_nr_records()`` returns the number of raw records in a file.

.. code-block:: python

    from bibliography_io import load_df
    from bibliography_io import load_primary_df

    normalized = load_df("references.ris")
    primary = load_primary_df("references.bib")

Raw records have not been curated as primary records. Normalization belongs to
``load()`` and is generic unless a source is selected. Formats retain their own
limits on what parser-level information can be represented. Unlike ``load()``,
``load_primary()`` and ``loads_primary()`` assume records are already
controlled: IDs are unique, non-empty strings; ``ENTRYTYPE`` values are valid,
non-empty strings; and ordinary field values are strings. Other value types
raise ``RecordValidationError`` rather than being stringified, combined,
deduplicated, or removed. Mapping and list values are retained only for BibTeX
fields explicitly declared with ``mapping_fields`` and ``list_fields``. These
declarations do not change the behavior of ``load()``. The same value contract
applies when writing a mapping with ``primary=True``.

Format examples
---------------

String loaders require an explicit format. Use ``loads_raw()`` to inspect
format-specific field names and parser-level values; use ``loads()`` for
normalized, ID-indexed records. In normalized records, authors are combined
into one ``author`` string joined by the word ``and``.

.. code-block:: python

    from bibliography_io import loads, loads_raw

    bib = """\
    @article{g2021,
      title  = {Trust},
      author = {Guo, Wenbo and Straub, Detmar},
    }
    """
    loads_raw(bib, format="bib")
    # [
    #     {
    #         'ID': 'g2021',
    #         'ENTRYTYPE': 'article',
    #         'title': 'Trust',
    #         'author': 'Guo, Wenbo and Straub, Detmar',
    #     }
    # ]

    ris = """\
    TY  - JOUR
    TI  - Trust
    AU  - Guo, Wenbo
    AU  - Straub, Detmar
    ER  -
    """
    loads_raw(ris, format="ris")
    # [
    #     {
    #         'TY': 'JOUR',
    #         'TI': 'Trust',
    #         'AU': ['Guo, Wenbo', 'Straub, Detmar'],
    #     }
    # ]
    loads(ris, format="ris")
    # [
    #     {
    #         'ENTRYTYPE': 'article',
    #         'title': 'Trust',
    #         'author': 'Guo, Wenbo and Straub, Detmar',
    #     }
    # ]

    json_text = """[
      {
        "title": "Trust",
        "authors": ["Guo, Wenbo", "Straub, Detmar"],
        "metadata": {"rank": 1}
      }
    ]"""
    loads_raw(json_text, format="json")
    # [
    #     {
    #         'title': 'Trust',
    #         'authors': ['Guo, Wenbo', 'Straub, Detmar'],
    #         'metadata': {'rank': 1},
    #     }
    # ]
    loads(json_text, format="json")
    # [
    #     {
    #         'title': 'Trust',
    #         'author': 'Guo, Wenbo and Straub, Detmar',
    #         'metadata': "{'rank': 1}",
    #         'ENTRYTYPE': 'misc',
    #     }
    # ]

Structured BibTeX fields
------------------------

Provenance mappings and lists can be written to BibTeX when callers explicitly
declare their field names. A mapping value is a Python dictionary from field
names to ``{"source": ..., "note": ...}`` dictionaries. Nested arbitrary
mappings are not supported. List values are Python lists of strings. Each
provenance or list item is serialized in the legacy semicolon-delimited form.

.. code-block:: python

    from bibliography_io import to_string
    from bibliography_io import loads_raw

    provenance = {
        "author": {"source": "ebsco_bib.bib/11111111111111111", "note": ""},
        "title": {"source": "manual.bib/entry1", "note": "checked"},
    }
    records = {
        "example": {
            "ENTRYTYPE": "article",
            "colrev_masterdata_provenance": provenance,
        }
    }
    text = to_string(
        records,
        format="bib",
        mapping_fields=["colrev_masterdata_provenance"],
    )
    restored = loads_raw(
        text,
        format="bib",
        mapping_fields=["colrev_masterdata_provenance"],
    )

The mapping is written as entries such as ``author:source;;``; list values are
written as semicolon-terminated items. The file APIs accept the same options.
Mapping and list values must follow these provenance conventions; values that
cannot be represented with the delimiters raise ``SerializationError``.
Structured-field options supplied to non-BibTeX formats raise
``UnsupportedFormatError``. See :doc:`design` for the full format contract.

BibTeX field ordering
---------------------

BibTeX output uses a CoLRev-oriented field order by default: origin, status,
provenance, PDF and screening metadata, file and exclusion metadata, DOI and
identifiers, then bibliographic fields. This default order is
``colrev_origin``, ``colrev_status``, ``colrev_masterdata_provenance``,
``colrev_data_provenance``, ``colrev_pdf_id``, ``screening_criteria``, ``file``,
``prescreen_exclusion``, ``doi``, ``grobid-version``, ``colrev.dblp.dblp_key``,
``colrev.semantic_scholar.id``, ``colrev.web_of_science.unique-id``,
``author``, ``booktitle``, ``journal``, ``title``, ``year``, ``volume``,
``number``, ``pages``, ``editor``, ``publisher``, ``url``, and ``abstract``.
Fields not in this list are written alphabetically after the CoLRev-ordered
fields. Pass ``field_order`` to ``to_string()`` or ``write()`` to choose a
different preferred order; all remaining fields are still written
alphabetically. Set ``sort_fields=False`` to preserve the input order of all
fields, including the predefined or explicitly ordered fields:

.. code-block:: python

    bibtex = to_string(
        records,
        format="bib",
        field_order=["author", "title", "year", "doi"],
    )

    original_order = to_string(records, format="bib", sort_fields=False)

Field names in ``field_order`` are normalized like record field names. The
``sort_fields`` option defaults to ``True`` and applies to BibTeX output;
non-BibTeX writers are unaffected.

BibTeX fields use a fixed 28-character field-name column, followed by two
spaces and ``=``. Longer names extend beyond the aligned column. Fixed padding
keeps the whitespace on other fields unchanged as fields are added or renamed,
which helps preserve Git history diffs.
