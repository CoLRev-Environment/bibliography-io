bibliography-io
===============

``bibliography-io`` provides standalone APIs for loading and writing
bibliographic records. Using the base installation does not require CoLRev or
GROBID.

Installation
------------

Install the base bibliography-io package with:

.. code-block:: console

   python -m pip install bibliography-io

Optional dependencies enable Markdown parsing and Excel file support:

.. code-block:: console

   python -m pip install "bibliography-io[markdown]"
   python -m pip install "bibliography-io[excel]"
   python -m pip install "bibliography-io[all]"  # both

Markdown parsing uses CoLRev and GROBID and requires a running GROBID service.
Excel loading and writing require the ``excel`` extra. Markdown table writing
is included in bibliography-io without an extra.

Quick example
-------------

.. code-block:: python

   from bibliography_io import load_raw, write

   records = load_raw("references.bib")
   write(records, path="references.ris")

File APIs infer formats from recognized filename suffixes. String APIs require
an explicit format:

.. code-block:: python

    from bibliography_io import to_string
    from bibliography_io import loads_raw

    records = loads_raw("@article{example, title={An example}}", format="bib")
    bibtex = to_string(records, format="bib")

See :doc:`usage` for supported formats, :doc:`api` for the public interface,
:doc:`source_extensions` for CoLRev source hooks, and :doc:`design` for the
standalone API and compatibility contract.

.. toctree::
   :maxdepth: 2
   :caption: Documentation

   usage
   api
   source_extensions
   design
   development
