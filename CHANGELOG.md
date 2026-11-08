# Changelog

Notable changes to bibliography-io are documented here.

## 0.4.0 — 2026-11-08

### Added

- Add an opt-in `missing_ok` option to `load_raw()` and `load()` for
  treating missing paths as empty results while preserving strict behavior by
  default.
- Document missing-path behavior across the raw, normalized, and primary
  loading APIs.

## 0.3.0 — 2026-11-08

### Added

- Add optional Markdown reference-list parsing through `grobid-tei`.
- Configure the GROBID service URL with `BIBLIOGRAPHY_IO_GROBID_URL`,
  defaulting to `http://localhost:8070`.
- Expose `fix_bib_file()` in the public API to repair malformed BibTeX files.

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
