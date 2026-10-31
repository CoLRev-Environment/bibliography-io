Source extensions for bibliography-io
=====================================

``bibliography-io`` can use installed CoLRev search-source packages to adapt
source-specific exports. Using bibliography-io without selecting a source does
not require CoLRev; packages are discovered only when a source is requested with
``load()`` or ``loads()``.

Package discovery
-----------------

CoLRev search-source packages register their endpoint class in the ``colrev``
entry-point group under the ``search_source`` name. For example:

.. code-block:: toml

   [project.entry-points.colrev]
   search_source = "example_package.source:ExampleSearchSource"

The caller passes the class's unique ``endpoint`` value as ``source``:

.. code-block:: python

   records = bibliography_io.load(
       "references.ris",
       source="colrev.example",
       source_version="2026",
   )

The package class's ``endpoint`` is used for discovery. Its CoLRev
``source_identifier`` describes a source record's unique-ID field and is not
used by bibliography-io to choose a package. If the requested endpoint is not
installed, ``OptionalBackendUnavailableError`` is raised. Multiple installed
classes claiming the same endpoint raise ``BackendExecutionError``.

Loading hooks
-------------

The selected class receives ``format`` and the optional ``source_version`` on
each hook call. The format identifies the input representation, while source
version identifies provider-specific export conventions.

Text input uses ``preprocess()`` before parsing:

.. code-block:: python

   @classmethod
   def preprocess(
       cls, text: str, *, format: str, source_version: str | None
   ) -> str:
       return text

Its default implementation returns the input text unchanged. This hook applies
to text formats such as BibTeX, RIS, CSV, and NBIB.

File-based input uses ``preprocess_file()`` before parsing:

.. code-block:: python

   @classmethod
   def preprocess_file(
       cls,
       path: Path,
       *,
       format: str,
       source_version: str | None,
       output_dir: Path,
   ) -> Path:
       return path

Its default implementation returns the original path. It is currently used for
Excel formats, whose binary workbooks are parsed from a path rather than text.
If a package transforms a file, it must leave the original unchanged, write the
transformed file under ``output_dir``, and return that file's path. The returned
path must exist and be either the original file or inside ``output_dir``.
Bibliography-io parses it before cleaning up the temporary directory, including
when parsing or a later hook raises an error.

Normalization and pipeline
--------------------------

After parsing, bibliography-io calls the selected class's normalization hook:

.. code-block:: python

   @classmethod
   def normalize(
       cls,
       records: list[dict],
       *,
       format: str,
       source_version: str | None,
   ) -> dict[str, dict]:
       ...

The hook receives parser-level records and returns a mapping keyed by record
ID. Each key must be a non-empty string matching that record's ``ID`` field.
The CoLRev ``SearchSourcePackageBaseClass`` default implementation assigns IDs
where needed, ensures they are unique, and indexes the records. Bibliography-io
validates and returns this ID-indexed mapping from ``load()`` or ``loads()``.
Source-specific field mapping and value transformation belong in this hook. The
hook must normalize field names; before return, bibliography-io converts every
non-string field value to a string, so callers can rely on normalized
string-valued fields from ``load()`` and ``loads()`` regardless of the hook's
intermediate value types.

In brief, the pipeline is:

1. Resolve the format and discover the requested endpoint.
2. Apply ``preprocess()`` to text input or ``preprocess_file()`` to file-based
   input.
3. Parse raw records using the format parser.
4. Apply source normalization and return the records as an ID-indexed mapping.

Without ``source``, ``load()`` skips source hooks and applies generic
normalization. The raw ``load_raw()`` and ``loads_raw()`` APIs bypass source
hooks and return parser-level records. ``loads()`` supports source hooks for
text input; Excel requires a file path and is not supported by ``loads()``.

For the public function signatures and return types, see :doc:`api`. For
user-facing loading examples, see :doc:`usage`.
