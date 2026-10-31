# Changelog

Notable changes to bibliography-io are documented here.

## 0.2.0 — 2026-10-31

### Added

- Separate raw and normalized loading APIs, including ID-indexed mappings for
  normalized records.
- BibTeX repair and cross-reference helpers, with support for primary-record
  loading and writing.
- Configurable field ordering and record sorting during serialization.

### Improved

- Preserve unknown and namespaced fields, repeated NBIB publication-type tags,
  and raw RIS type tags more consistently.
- Improve normalization and validation behavior across supported formats.
- Expand standalone API and installed-wheel coverage.
