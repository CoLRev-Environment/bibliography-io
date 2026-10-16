API reference
=============

The strict standalone public API is:

File operations infer formats from filename suffixes unless an explicit
``format`` is provided. String operations require ``format``. See
:doc:`usage` for the read/write format matrix, including the distinction
between core Markdown table output and pending optional reference-list parsing.

.. autofunction:: bibliography_io.load_records

.. autofunction:: bibliography_io.loads

.. autofunction:: bibliography_io.write_records

.. autofunction:: bibliography_io.dumps

The historical names ``load``, ``write``, ``write_file``, ``to_string``,
``load_df``, and ``get_nr_records`` are deprecated immediately. They remain
available during migration and will be removed in a future release.
