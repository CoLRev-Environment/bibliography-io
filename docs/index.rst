bibliography-io
===============

``bibliography-io`` loads and writes bibliographic records in common reference
formats, including BibTeX, RIS, CSV, Excel, Markdown, EndNote, NBIB, and JSON.
It uses CoLRev's shared metadata definitions for loading and writing records.

Installation
------------

Install the ``colrev`` extra to use the load and write functions:

.. code-block:: console

   python -m pip install "bibliography-io[colrev]"

Quick example
-------------

.. code-block:: python

   from pathlib import Path

   from bibliography_io import load_records, write_records

   records = load_records(filename=Path("references.bib"))
   write_records(records, filename=Path("references.ris"))

The package can also be installed without the ``colrev`` extra, but loading and
writing records requires it. See :doc:`usage` for more examples and
:doc:`api` for the generated API reference.

.. toctree::
   :maxdepth: 2
   :caption: Documentation

   usage
   api
