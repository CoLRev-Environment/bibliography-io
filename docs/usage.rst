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
declared structured BibTeX mappings and lists remain structured.

Structured BibTeX fields
------------------------

Nested mappings and lists can be written to BibTeX when callers explicitly
declare their field names. Use ``mapping_fields`` for top-level mappings and
``list_fields`` for top-level lists; nested lists/mappings within those values
are preserved automatically.

.. code-block:: python

    from bibliography_io import to_string
    from bibliography_io import loads_raw

    provenance = {"CURATED": {"source": "github...", "note": ""}}
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

The file APIs accept the same options. The ``bibio-json-v1:`` encoding uses
compact JSON encoded as UTF-8 and Base64 inside a standard BibTeX braced value.
It preserves JSON strings, delimiters, braces, quotes, backslashes, Unicode,
booleans, numbers, nulls, and empty/nested containers. Undeclared mappings and
lists still raise ``SerializationError``. Structured-field options supplied to
non-BibTeX formats raise ``UnsupportedFormatError``. See :doc:`design` for the
full encoding and error contract.
