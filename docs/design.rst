Design principles
==================

Purpose and scope
-----------------

Bibliography I/O supports literature-review workflows that collect
bibliographic records from multiple sources. Those sources may use different
formats, such as RIS and BibTeX, or different syntax versions and conventions
within the same format.

These workflows have two related but distinct kinds of data: **raw
records**, as received from a source, and **primary records**, which are
curated and maintained as the review's canonical dataset. They have
different requirements, so the package provides separate APIs for handling
them.

Bibliography I/O aims to give each API a consistent interface and in-memory
representation across supported formats, while accommodating source- and
version-specific differences. Today, format-specific packages often expose
different interfaces and outputs, and may not distinguish raw records from
primary records. This makes it harder to combine sources and manage records
throughout a review.

Bibliography-io has no mandatory runtime dependencies and uses optional
backends where additional format support requires them. Its design is inspired
in part by Pandoc's approach to working across formats through a common
interface.

Raw data API
------------

Bibliographic data comes from databases and other providers, so formats and the
ways those formats are used are not always under strict control. The raw data
API is designed to be robust to that variation across supported formats and to
write output that different consumers can import.

Raw loading returns ordered lists and preserves parser-level field names and
value types. Generic or source-specific normalization is selected through the
convenience ``load()`` interface:

.. code-block:: python

   load_raw(path, *, format=None, mapping_fields=(), list_fields=()) -> list[dict]
   loads_raw(string, *, format=..., mapping_fields=(), list_fields=()) -> list[dict]
   load(path, *, source=None, source_version=None, format=None) -> dict[str, dict]
   loads(text, *, format=..., source=None, source_version=None) -> dict[str, dict]

The corresponding writing interfaces are:

.. code-block:: python

   write(
       records, *, path, format=None, mapping_fields=(), list_fields=(),
       primary=False
   ) -> None
   to_string(
       records, *, format, mapping_fields=(), list_fields=()
   ) -> str

The raw API follows these principles:

- File APIs infer the format from a recognized suffix when ``format`` is omitted.
  Supply ``format`` when the suffix is ambiguous or does not match the file's
  actual format. String APIs require an explicit format. An unknown or
  unsupported format raises ``UnsupportedFormatError``.
- Raw loading does not require record IDs to be present or unique. Raw parsing
  does not generate IDs. Accordingly, loading returns a list rather than an
  ID-indexed dictionary, preserving source order and every record. This may
  mean slower lookups by ID.
- Unknown fields are preserved and are not silently discarded. If the selected
  destination format cannot represent a field or value, writing raises
  ``SerializationError``.
- ``load_raw()`` and ``loads_raw()`` return parser-level values, including
  repeated fields as lists and structured values as mappings where the format
  supports them. They do not normalize field names or values and do not assign
  IDs.
- ``load()`` applies generic normalization unless a source is supplied, in
  which case source-specific preprocessing and field normalization are used.
  Both ``load()`` and ``loads()`` return records indexed by unique, non-empty
  string IDs and raise ``MissingRecordIDError`` or ``DuplicateRecordIDError`` if
  normalization does not produce valid IDs. The mapping supports processing
  imported records as primary records, including merging and processing them,
  while retaining IDs for back-tracing records to their imports.
  ``source_version`` optionally identifies provider/export conventions. These
  identifiers are distinct from ``format``, which describes the encoding. See
  :ref:`record-shape` for the public value-type guarantees.
- Source-specific parsing and normalization are provided by separately
  installable packages that extend bibliography-io as plugins. They may map
  fields and interpret source/version-specific values. See
  :ref:`source-specific-parsing` for the loading pipeline.
- Metadata preparation (e.g., of author and language fields), and lookup
  searches are responsibilities of downstream packages.

File writes replace the destination. Markdown table writing is built into
bibliography-io; Markdown reference-list parsing is an optional, lazily loaded
backend. Format-specific options for raw loading and writing, including options
for JSON and other formats built into bibliography-io, belong to this API and
must be documented with the relevant format. Public bibliography-io functions
accept no undocumented options. Structured BibTeX field options for primary
data are described in the Primary Data API section.

.. _source-specific-parsing:

Source-specific parsing
~~~~~~~~~~~~~~~~~~~~~~~

The ``load()`` and ``loads()`` APIs can apply source-specific processing from an
installed CoLRev search-source package. Without ``source``, ``load()`` uses
generic normalization. With ``source``, bibliography-io discovers the package
by its unique endpoint identifier (for example, ``colrev.crossref``) and passes
the optional ``source_version`` through its hooks. This endpoint is distinct
from the package's ``source_identifier``, which describes record fields and is
not used for package selection.

Bibliography-io owns the loading pipeline:

1. Resolve the input format.
2. For text inputs, allow the package to preprocess the text; for file-based
   inputs, allow it to return the original path or a transformed temporary file.
3. Parse the resulting input into parser-level records.
4. Apply source-specific normalization and return the ID-indexed record mapping.

The source normalizer returns an ID-keyed mapping, which bibliography-io
validates and returns. Without a source, bibliography-io applies generic
normalization and indexes the validated records by ID. This mapping facilitates
processing imported records as primary records (which may then be merged and
processed) and back-tracing records using their IDs. The raw ``load_raw()`` and
``loads_raw()`` APIs bypass source hooks and expose parser-level records as lists.
Source extensions are optional, so using bibliography-io without a selected
source does not require CoLRev. See :doc:`source_extensions` for package
registration, hook contracts, and file-preprocessing details.

Primary Data API
----------------

Primary data is maintained as a curated set: every record is expected to have
an ID that is unique within the primary dataset and an entry type. It may have additional and provenance information in mapping or list format.

The primary-data interfaces are:

.. code-block:: python

   load_primary(
       path, *, format=None, header_only=False, mapping_fields=(), list_fields=()
   ) -> dict[str, dict]

   loads_primary(
       text, *, format=..., mapping_fields=(), list_fields=()
   ) -> dict[str, dict]

   write(
       records, *, path, format=None, primary=True,
       mapping_fields=(), list_fields=()
   ) -> None

The primary-data API follows these principles:

- Primary loaders accept supported input formats and return records indexed by
  ID. Pass ``primary=True`` to ``write()`` to validate primary records and
  restrict writing to BibTeX. Primary records are written in ascending ID
  order; ordinary/raw writes preserve the supplied record order.
- Loads return an ID-indexed dictionary. Every record must have a valid, unique
  string ``ID``; missing and duplicate IDs raise ``MissingRecordIDError`` and
  ``DuplicateRecordIDError``, respectively. The API does not generate IDs or
  silently overwrite duplicate records. ID assignment and validation belong to
  the caller's ingestion or promotion process.
- Use ``loads_primary()`` to load versioned bibliography supplied as text, such as
  content read from a particular Git revision. It parses the text and returns
  records indexed by ID.
- ``load_primary(header_only=True)`` is a performance-oriented option for
  workflows that need only record headers. It returns the same ID-indexed
  dictionary shape with only ``ID`` and ``ENTRYTYPE`` in each record; the default
  ``False`` returns complete records.
- Entry types are open, lowercase strings.
- See :ref:`record-shape` for the primary loader's field-value contract.
- ``mapping_fields`` and ``list_fields`` declare BibTeX fields that contain
  provenance mappings and string lists, respectively. These options are
  available for primary writes and ordinary/raw writes.

Structured fields
~~~~~~~~~~~~~~~~~

The BibTeX loading and writing interfaces support ``mapping_fields`` and
``list_fields``. These field-name iterables declare BibTeX fields whose Python
values are dictionaries or lists. Declared fields are matched case-insensitively
against BibTeX field names. Values must have the declared top-level type. Fields
cannot be declared as both mappings and lists. Mappings are specifically for
provenance in the shape ``{field: {"source": str, "note": str}}``; arbitrary
nested mappings are not supported. Lists contain strings. Dots are accepted in
BibTeX field keys and preserved by BibTeX loading and writing.

The existing ``colrev_origin`` convention stores references to contributing raw
records as a list in the record data and writes them in BibTeX as a
semicolon-delimited value. For example, a primary record produced by
deduplicating records loaded through the Raw Data API may contain:

.. code-block:: python

   record = {
       "ID": "merged-1",
       "ENTRYTYPE": "article",
       "title": "An example",
       "colrev_origin": [
           "CROSSREF.bib/001792",
           "DBLP.bib/001703",
       ],
   }

The corresponding BibTeX representation is:

.. code-block:: bibtex

   @article{merged-1,
     title = {An example},
   colrev_origin = {CROSSREF.bib/001792;
                    DBLP.bib/001703;},
   }

Each locator identifies an individual raw record that contributed to the
deduplicated primary record. This is an example of the existing ``colrev_origin``
convention, not a requirement for a particular ``colrev_*`` provenance field.
Provenance mappings use the legacy ``field:source;note;`` representation, one
entry per line. An empty note therefore yields ``field:source;;``. List values
use one semicolon-terminated item per line. Both are wrapped in ordinary
BibTeX braces, and each emitted BibTeX field ends with a comma, including the
last field in an entry. Semicolons, braces, and newlines are reserved delimiters
and are rejected inside source, note, and list-item values. Empty mappings and
lists are written as empty braced values. The loader parses these forms back
into Python dictionaries and lists when the corresponding fields are declared.

BibTeX field names are padded to a fixed width of 28 characters before the two
spaces preceding ``=``. This width matches ``colrev_masterdata_provenance``;
longer field names extend past the aligned column. Fixed-width padding keeps
unrelated field lines stable when fields are added or renamed, helping preserve
useful Git history diffs.

Only fields explicitly declared with ``mapping_fields`` or ``list_fields`` may
contain mapping/list values when writing BibTeX. Undeclared mappings, lists,
tuples, and sets raise ``SerializationError``. Values that cannot be represented
with the provenance delimiters raise ``SerializationError``.

Exceptions
----------

The standalone API raises the following exceptions:

.. list-table::
   :header-rows: 1

   * - Exception
     - Raised when
   * - ``TypeError``
     - An argument has an invalid Python type or required arguments are missing.
   * - ``FileNotFoundError``
     - A file-loading operation receives a path that does not exist as a file.
   * - ``OSError`` / ``UnicodeDecodeError``
     - Reading or writing a file fails, or file contents are not valid UTF-8.
   * - ``UnsupportedFormatError``
     - A bibliography-io operation requests an unknown or unsupported format, or a CoLRev search-source package does not support the requested source/format/version combination.
   * - ``ParseError``
     - Input cannot be parsed as the selected format. Underlying parser errors are chained when available.
   * - ``RecordValidationError``
     - A record, structured-field declaration, or source-tag combination does not conform to the API's validation rules.
   * - ``MissingRecordIDError``
     - A primary-data dictionary operation encounters a record with no valid ID.
   * - ``DuplicateRecordIDError``
     - A primary-data dictionary operation encounters an ID more than once.
   * - ``SerializationError``
     - A record or field value cannot be represented in the requested output format.
   * - ``OptionalBackendUnavailableError``
     - A requested optional parsing or writing backend, including a CoLRev search-source package, is not installed.
   * - ``BackendExecutionError``
     - An installed optional backend or CoLRev search-source package fails while parsing or writing.

All package-defined exceptions inherit from ``BibliographyIOError``. Raw
list-based parsing preserves records without applying primary-data ID
uniqueness requirements. Compatibility adapters may additionally expose errors
from their underlying services; such service errors are propagated without
translation.

Compatibility policy
--------------------

Historical CoLRev callbacks and options (``entrytype_setter``, ``field_mapper``,
``unique_id_field``, ``id_labeler``, ``logger``, and ``empty_if_file_not_exists``) are
CoLRev adapter behavior, not bibliography-io API options. The legacy ``format_names`` option
has been removed. CoLRev's adapter is responsible for callback ordering and
legacy missing-file defaults. Historical ``colrev.loader.*`` and
``colrev.writer.*`` imports remain CoLRev compatibility facades during migration;
they are not bibliography-io public module paths.

The legacy processing modules ``load_utils_formatter.py`` and
``load_utils_name_formatter.py`` contain CoLRev-specific formatting and name
parsing behavior. Their functionality should be integrated into CoLRev
packages, not maintained as bibliography-io functionality. In particular,
language-code interpretation and normalization belong in CoLRev packages.

The legacy ``bibliography_io.loader.load_utils`` adapter has been removed.
Callers should use ``load_raw()`` or ``loads_raw()`` for raw list-based parsing;
CoLRev-specific callbacks, ID assignment, missing-file defaults, and workflow
processing belong in CoLRev packages.
