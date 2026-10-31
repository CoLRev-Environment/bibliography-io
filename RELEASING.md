# Releasing

The current release target is `0.2.0`. Keep the project version, release notes,
and Git tag synchronized when preparing a release.

## Required pre-release checks

1. Ensure the CI test job passes for the supported Python versions. It installs
   `bibliography-io` and its test extra without optional integration packages,
   then runs the complete standalone test suite:

   ```shell
   python -m pip install -e ".[test]"
   pytest
   ```

   The test suite exercises the public bibliography-io API and repository data
   fixtures without importing optional integration packages.
2. Build and validate the release artifacts, then install the wheel into a clean
   environment without optional extras:

   ```shell
   python -m pip install --upgrade build twine
   python -m build
   python -m twine check dist/*
   python -m venv /tmp/bibliography-io-wheel-smoke
   /tmp/bibliography-io-wheel-smoke/bin/python -m pip install dist/*.whl
   ```

   From outside the source checkout, smoke-test imports and a BibTeX file
   round-trip with the installed wheel. The wheel test must not install the
   optional extras.
3. Built-in Markdown table output is part of the default test suite. Test
   Markdown reference-list parsing with the ``markdown`` extra and Excel
   load/write with the ``excel`` extra. The installed-wheel smoke test should
   continue to run without extras.
4. Update `project.version` in `pyproject.toml`, add release notes, and keep the
   version in the Git tag synchronized with package metadata.

## TestPyPI verification

Upload the built artifacts and test installation of the base bibliography-io
package without optional extras:

```shell
python -m twine upload --repository testpypi dist/*
python -m venv /tmp/bibliography-io-testpypi
/tmp/bibliography-io-testpypi/bin/python -m pip install \
    --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    "bibliography-io==0.2.0"
```

Repeat the installed-wheel smoke test against the TestPyPI installation. The
`--extra-index-url` allows runtime dependencies not mirrored on TestPyPI to
resolve from PyPI.

## PyPI publication with GitHub Actions

`.github/workflows/publish.yml` builds distributions and publishes them to PyPI
when a GitHub Release is published. Before using it:

1. Create the `bibliography-io` project on PyPI and configure a Trusted
   Publisher for this repository, the `publish.yml` workflow, and the `pypi`
   environment.
2. Create the matching GitHub `pypi` environment and configure any required
   protection rules.
3. Publish only after CI and TestPyPI verification pass. Use a `v<version>` tag
   matching `project.version` (for example, `v0.2.0`).

## Compatibility status

The standalone bibliography-io API and its format-specific data fixtures are
covered without CoLRev or GROBID. Historical CoLRev-facing compatibility
wrappers are outside the standalone test suite. Markdown reference-list parsing
is optional and remains unverified until its backend is finalized and tested.
