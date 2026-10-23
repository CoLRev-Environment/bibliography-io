"""Exceptions raised by bibliography-io's standalone APIs."""


class BibliographyIOError(Exception):
    """Base class for package-defined I/O errors."""


class UnsupportedFormatError(BibliographyIOError, ValueError):
    """A requested format is not supported for the operation."""


class ParseError(BibliographyIOError, ValueError):
    """Input is malformed or cannot be parsed."""


class RecordValidationError(BibliographyIOError, ValueError):
    """A record does not conform to the record contract."""


class MissingRecordIDError(RecordValidationError):
    """A record is missing an ID where one is required."""


class DuplicateRecordIDError(RecordValidationError):
    """Two records have the same ID."""


class SerializationError(BibliographyIOError, ValueError):
    """Records cannot be written in the requested output format."""


class OptionalBackendUnavailableError(BibliographyIOError, ImportError):
    """An optional format backend is not installed."""


class BackendExecutionError(BibliographyIOError):
    """An optional backend failed while processing input."""
