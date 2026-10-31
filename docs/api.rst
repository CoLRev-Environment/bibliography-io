API reference
=============

The strict standalone public API is:

File operations infer formats from filename suffixes unless an explicit
``format`` is provided. String operations require ``format``. See
:doc:`usage` for the read/write format matrix, including the distinction
between built-in Markdown table output and pending optional reference-list
parsing.

Loading API
-----------

Raw loaders return an ordered list of record dictionaries with parser-level
field names and values (for example, strings, lists, or mappings). They do not
apply normalization or assign IDs.

.. py:function:: bibliography_io.load_raw(path, *, format=None, mapping_fields=(), list_fields=())

.. py:function:: bibliography_io.loads_raw(string, *, format, mapping_fields=(), list_fields=())

``mapping_fields`` and ``list_fields`` declare structured BibTeX fields.
File operations infer ``format`` from the suffix unless supplied explicitly;
string operations require it.

The convenience loaders apply generic normalization when ``source`` is omitted.
If ``source`` is supplied, they select an installed CoLRev search-source package
by its unique endpoint identifier (for example, ``colrev.crossref``).
``source_version`` is an optional export-version label. Both normalized loaders
return a dictionary keyed by unique, non-empty record IDs; invalid or duplicate
IDs raise ``MissingRecordIDError`` or ``DuplicateRecordIDError``. This mapping
supports processing imports as primary records, including merging and processing
them, while retaining IDs for back-tracing. File suffixes are used to infer the
format unless ``format`` is supplied; pass ``format`` when the suffix is
ambiguous or does not match the file's actual format. Use the raw loading APIs
for parser-level values.

For the return-value contracts of the raw, normalized, and primary loaders, see
the :ref:`record-shape` section in :doc:`usage`.

.. py:function:: bibliography_io.load(path, *, source=None, source_version=None, format=None)

It returns an ID-indexed dictionary of record dictionaries, preserving source
order. CoLRev search-source packages register ``search_source`` entry points in
the ``colrev`` entry-point group; bibliography-io selects the package whose
``endpoint`` matches ``source``. Source-specific hook behavior and package
registration are described in :doc:`source_extensions`. A missing package raises
``OptionalBackendUnavailableError``.

.. py:function:: bibliography_io.loads(text, *, format, source=None, source_version=None)

It returns the same ID-indexed mapping contract as ``load()`` for text input.

``load_df()`` calls ``load()`` and returns its normalized records as DataFrame
rows. Parser-level data is available through the list-returning raw APIs rather
than a raw DataFrame helper.

.. autofunction:: bibliography_io.load_primary

.. autofunction:: bibliography_io.loads_primary

.. autofunction:: bibliography_io.write

.. autofunction:: bibliography_io.to_string

.. autofunction:: bibliography_io.load_df

.. autofunction:: bibliography_io.load_primary_df

.. autofunction:: bibliography_io.get_nr_records
