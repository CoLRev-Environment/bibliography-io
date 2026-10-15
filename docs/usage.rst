Usage
=====

File APIs infer the format from a recognized suffix. They accept strings or
``pathlib.Path`` objects, read and write UTF-8 text, and raise
``FileNotFoundError`` for missing input paths.

.. code-block:: python

   from bibliography_io import load_records, write_records

   records = load_records("references.bib")
   write_records(records, "references.ris")

Pass ``format`` to override suffix inference. String APIs always require it:

.. code-block:: python

   from bibliography_io import dumps, loads

   records = loads("@article{example, title={An example}}", format="bib")
   bibtex = dumps(records, format="bib")

Core readers support BibTeX, RIS, CSV, Excel (``.xls`` and ``.xlsx``), ENL,
NBIB, and JSON. Core writers support BibTeX, RIS, CSV, Excel (``.xlsx``), and
Markdown tables. Markdown table writing is separate from optional Markdown
reference-list parsing. The latter uses a lazily discovered entry point in
``bibliography_io.backends`` named ``markdown``; without one,
``OptionalBackendUnavailableError`` is raised when Markdown input is requested.

Records are ordered mappings keyed by string ``ID`` values. Each record has
``ID`` and ``ENTRYTYPE`` fields. Source IDs are preserved, missing IDs are
assigned sequentially without collisions, and duplicate IDs are rejected.
Unknown fields are retained when the output format can represent them.

The historical root functions ``load``, ``write``, ``write_file``,
``to_string``, ``load_df``, and ``get_nr_records`` are deprecated immediately.
They remain available during migration and will be removed in a future release.
