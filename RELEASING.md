# Releasing

The initial release version proposed for this project is `0.1.0`. Before
publishing, confirm that version and the package name with the maintainers.

## Pre-release checks

1. Make sure the release changes are merged to the default branch and the CI
   checks pass.
2. The current CI exercises `tests/test_public_api.py`; the legacy tests under
   `tests/2_loader` call into CoLRev internals and the Markdown integration test
   expects a local GROBID service. Before describing the full loader suite as
   supported, adapt those tests to the published API and provide the required
   services, or document the supported CoLRev version and test setup.
3. Update `project.version` in `pyproject.toml` and add release notes to the
   GitHub release. This project currently uses a static version; keep the
   version in `pyproject.toml` and the Git tag in sync.
4. Build and validate the exact artifacts that will be released:

   ```shell
   python -m pip install --upgrade build twine
   python -m build
   python -m twine check dist/*
   ```

5. Upload the artifacts to TestPyPI and verify installation in a clean virtual
   environment. Use a TestPyPI token or configure TestPyPI Trusted Publishing:

   ```shell
   python -m twine upload --repository testpypi dist/*
   python -m pip install --index-url https://test.pypi.org/simple/ \
       --extra-index-url https://pypi.org/simple/ "bibliography-io[all]==0.1.0"
   ```

   Check that imports, load/write examples, and the published metadata work as
   expected. The `--extra-index-url` lets dependencies not mirrored on TestPyPI
   resolve from PyPI.

## PyPI publication with GitHub Actions

`.github/workflows/publish.yml` builds distributions and publishes them to PyPI
when a GitHub Release is published. Before using it:

1. Create the `bibliography-io` project on PyPI (or arrange the initial
   publisher account) and configure a PyPI Trusted Publisher for this GitHub
   repository, the `publish.yml` workflow, and the `pypi` environment.
2. Create the matching `pypi` GitHub environment. Add any required protection
   rules or reviewers according to the maintainers' release policy.
3. Publish a GitHub Release only after TestPyPI verification. The release tag
   should be `v<version>` (for example, `v0.1.0`) and match
   `project.version` in `pyproject.toml`.

The workflow publishes to the live PyPI project; TestPyPI upload and verification
are intentionally a pre-release step. The PyPI project owner, exact release date,
and release approval policy remain maintainer decisions.
