bibliography-io
===============

``bibliography-io`` provides standalone APIs for loading and writing
bibliographic records. Core use does not require CoLRev or GROBID.

Installation
------------

Install the core package with:

.. code-block:: console

   python -m pip install bibliography-io

The optional ``colrev`` extra is for legacy compatibility modules, not the
standalone core API. Markdown reference-list parsing is pending an optional
backend; Markdown table writing is included in the core.

Quick example
-------------

.. code-block:: python

   from bibliography_io import load_records, write_records

   records = load_records("references.bib")
   write_records(records, path="references.ris")

File APIs infer formats from recognized filename suffixes. String APIs require
an explicit format:

.. code-block:: python

   from bibliography_io import dumps, loads

   records = loads("@article{example, title={An example}}", format="bib")
   bibtex = dumps(records, format="bib")

See :doc:`usage` for supported formats and :doc:`api` for the public interface.

.. toctree::
   :maxdepth: 2
   :caption: Documentation

   usage
   api
