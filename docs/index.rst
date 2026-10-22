bibliography-io
===============

``bibliography-io`` provides standalone APIs for loading and writing
bibliographic records. Core use does not require CoLRev or GROBID.

Installation
------------

Install the core package with:

.. code-block:: console

   python -m pip install bibliography-io

Optional dependencies enable Markdown parsing and Excel file support:

.. code-block:: console

   python -m pip install "bibliography-io[markdown]"
   python -m pip install "bibliography-io[excel]"
   python -m pip install "bibliography-io[all]"  # both

Markdown parsing uses CoLRev and GROBID and requires a running GROBID service.
Excel loading and writing require the ``excel`` extra. Markdown table writing
is included in the core package.

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

See :doc:`usage` for supported formats, :doc:`api` for the public interface,
and :doc:`design` for the standalone API and compatibility contract.

.. toctree::
   :maxdepth: 2
   :caption: Documentation

   usage
   api
   design
   development
