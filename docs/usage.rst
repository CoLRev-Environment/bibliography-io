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

Format aliases include ``bibtex`` for BibTeX, ``excel`` for Excel, ``endnote``
for ENL, and ``markdown`` for Markdown. File suffixes are case-insensitive.

Markdown forms and optional dependencies
-----------------------------------------

Markdown table output is core functionality and does not need an optional
backend. Markdown reference-list parsing uses CoLRev and GROBID and is enabled
by installing ``bibliography-io[markdown]``. A running GROBID service is also
required. Without the extra, a Markdown read raises
``OptionalBackendUnavailableError``. Excel loading and writing require
``bibliography-io[excel]``; the ``all`` extra installs both optional feature
sets.

Record shape
------------

Records are ordered mappings keyed by string ``ID`` values. Each record has
``ID`` and ``ENTRYTYPE`` fields. Source IDs are preserved; missing IDs are
assigned sequentially without collisions; duplicate IDs raise an error.
Unknown fields are retained where the output format can represent them.

DataFrame helpers
-----------------

``load_raw_df()`` returns raw records as DataFrame rows in source order, with a
default ``RangeIndex``. ``load_primary_df()`` returns primary records with IDs
as the DataFrame index. Both functions accept the corresponding options from
``load_raw()`` and ``load_primary()``. Pandas is optional; install the Excel
extra with ``pip install bibliography-io[excel]`` to use these helpers.

``get_nr_records()`` returns the number of raw records in a file.

.. code-block:: python

    from bibliography_io import load_primary_df
    from bibliography_io import load_raw_df

    raw = load_raw_df("references.ris")
    primary = load_primary_df("references.bib")

Loaded records are **raw** in the sense that they have not been curated as
primary records. ``load_raw`` and ``loads_raw`` return **normalized raw data**
by default, for convenient access and as a fallback representation. Pass
``normalize=False`` to access **non-normalized raw data** for maximum control
or source-specific processing:

.. code-block:: python

   convenient = load_raw("references.ris")
   source_values = load_raw("references.ris", normalize=False)

Normalized raw data uses canonical field names, removes empty repeated values,
deduplicates exact matches, and represents ordinary fields as strings. Multiple
authors are joined with ``" and "`` and keywords with ``"; "``. Distinct
non-empty repeated values for other fields are joined with ``"; "`` in their
source order. Non-normalized values retain source-level field names and
repeated-value structure where the format permits it; formats may have
different limits on what source information can be represented. Explicitly
declared BibTeX provenance mappings and lists retain their container types when
loaded with the corresponding field declarations.

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
Fields not in this list are appended in their original record order. Pass
``field_order`` to ``to_string()`` or ``write()`` to choose a different
priority; unlisted fields are still appended in their original order:

.. code-block:: python

    bibtex = to_string(
        records,
        format="bib",
        field_order=["author", "title", "year", "doi"],
    )

Field names in ``field_order`` are normalized like record field names. This
option is supported for BibTeX output only.

BibTeX fields use a fixed 28-character field-name column, followed by two
spaces and ``=``. Longer names extend beyond the aligned column. Fixed padding
keeps the whitespace on other fields unchanged as fields are added or renamed,
which helps preserve Git history diffs.
