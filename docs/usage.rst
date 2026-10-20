Usage
=====

File and string APIs
--------------------

File APIs accept a path as ``str`` or ``pathlib.Path``. They infer the format
from a recognized suffix, unless ``format`` is supplied explicitly. Reads use
UTF-8 and missing files raise ``FileNotFoundError``.

.. code-block:: python

   from pathlib import Path

   from bibliography_io import load_records, write_records

   records = load_records(Path("references.bib"))
   write_records(records, path="references.ris")

String APIs require an explicit ``format``:

.. code-block:: python

   from bibliography_io import dumps, loads

   records = loads("@article{example, title={An example}}", format="bib")
   bibtex = dumps(records, format="bib")

Supported formats
-----------------

``load_records`` reads BibTeX (``.bib``), RIS (``.ris``), CSV (``.csv``),
Excel (``.xls`` and ``.xlsx``), ENL/EndNote (``.enl`` and ``.txt``), NBIB
(``.nbib``), and JSON (``.json``). It also accepts Markdown (``.md``) for
reference-list parsing only when the optional backend is installed.

``write_records`` writes BibTeX, RIS, CSV, Excel (``.xlsx``), and Markdown
tables. JSON, ENL, NBIB, and legacy Excel (``.xls``) are read-only. ``dumps``
supports BibTeX, RIS, CSV, and Markdown-table output. Excel is a file-only
format; ``loads`` supports the text-based input formats.

Format aliases include ``bibtex`` for BibTeX, ``excel`` for Excel, ``endnote``
for ENL, and ``markdown`` for Markdown. File suffixes are case-insensitive.

Markdown forms and optional backend
-----------------------------------

Markdown table output is core functionality and does not need an optional
backend. Markdown reference-list parsing is a distinct feature. Its backend
and installation extra are still pending; until finalized, a Markdown read
without a registered ``bibliography_io.backends`` entry point named
``markdown`` raises ``OptionalBackendUnavailableError``.

Record shape
------------

Records are ordered mappings keyed by string ``ID`` values. Each record has
``ID`` and ``ENTRYTYPE`` fields. Source IDs are preserved; missing IDs are
assigned sequentially without collisions; duplicate IDs raise an error.
Unknown fields are retained where the output format can represent them.

Structured BibTeX fields
------------------------

Nested mappings and lists can be serialized in BibTeX when callers explicitly
declare their field names. Use ``mapping_fields`` for top-level mappings and
``list_fields`` for top-level lists; nested lists/mappings within those values
are preserved automatically.

.. code-block:: python

   from bibliography_io import dumps, loads

   provenance = {"CURATED": {"source": "github...", "note": ""}}
   records = {
       "example": {
           "ENTRYTYPE": "article",
           "colrev_masterdata_provenance": provenance,
       }
   }
   text = dumps(
       records,
       format="bib",
       mapping_fields=["colrev_masterdata_provenance"],
   )
   restored = loads(
       text,
       format="bib",
       mapping_fields=["colrev_masterdata_provenance"],
   )

The file APIs accept the same options. The ``bibio-json-v1:`` encoding uses
compact JSON encoded as UTF-8 and Base64 inside a standard BibTeX braced value.
It preserves JSON strings, delimiters, braces, quotes, backslashes, Unicode,
booleans, numbers, nulls, and empty/nested containers. Undeclared mappings and
lists still raise ``SerializationError``. Structured-field options supplied to
non-BibTeX formats raise ``UnsupportedFormatError``. See ``CONTRACT.md`` for the
full encoding and error contract.

Compatibility aliases
----------------------

The historical root functions ``load``, ``write``, ``write_file``,
``to_string``, ``load_df``, and ``get_nr_records`` are deprecated immediately.
They remain available during migration and will be removed in a future release.
