Development
===========

Install the package's test extra and run the standalone test suite. The tests
use the package API and do not require CoLRev:

.. code-block:: console

   python -m pip install -e ".[test]"
   python -m pip install build pre-commit
   pre-commit install
   pre-commit run --all-files
   pytest

Build the documentation locally with:

.. code-block:: console

   python -m pip install -e ".[docs]"
   python -m sphinx -W --keep-going -b html docs docs/_build/html

See `RELEASING.md <https://github.com/CoLRev-Environment/bibliography-io/blob/main/RELEASING.md>`_
for the package build and publication process.
