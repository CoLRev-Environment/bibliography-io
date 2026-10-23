API reference
=============

The strict standalone public API is:

File operations infer formats from filename suffixes unless an explicit
``format`` is provided. String operations require ``format``. See
:doc:`usage` for the read/write format matrix, including the distinction
between core Markdown table output and pending optional reference-list parsing.

.. autofunction:: bibliography_io.load_raw

.. autofunction:: bibliography_io.loads_raw

.. autofunction:: bibliography_io.load_primary

.. autofunction:: bibliography_io.loads_primary

.. autofunction:: bibliography_io.write

.. autofunction:: bibliography_io.to_string

.. autofunction:: bibliography_io.load_raw_df

.. autofunction:: bibliography_io.load_primary_df

.. autofunction:: bibliography_io.get_nr_records
