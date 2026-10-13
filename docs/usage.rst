Usage
=====

Load and write files
--------------------

The file extension determines the format. Records are returned as a dictionary
keyed by record ID.

.. code-block:: python

   from pathlib import Path

   from bibliography_io import load_records, write_records

   records = load_records(filename=Path("references.bib"))
   write_records(records, filename=Path("references.ris"))

Readers support BibTeX (``.bib``), RIS (``.ris``), CSV (``.csv``), Excel
(``.xls`` and ``.xlsx``), Markdown (``.md``), EndNote (``.enl`` and ``.txt``),
NBIB (``.nbib``), and JSON (``.json``). Writers support BibTeX, RIS, CSV,
Excel (``.xlsx``), and Markdown.

Use the shorter aliases ``load`` and ``write`` when using the package namespace:

.. code-block:: python

   from pathlib import Path

   import bibliography_io as bibio

   records = bibio.load(filename=Path("references.bib"))
   bibio.write(records, filename=Path("references.ris"))

The aliases ``load`` and ``write_file`` refer to ``load_records`` and
``write_records`` respectively.

Load from a string
------------------

Use :func:`bibliography_io.loads` when the input is already in memory. The
``implementation`` argument names the input format:

.. code-block:: python

   from bibliography_io import loads

   records = loads(
       "@article{example2024, title={An Example}, year={2024}}",
       implementation="bib",
   )

DataFrames and record counts
----------------------------

Use :func:`bibliography_io.load_df` to load records into a pandas DataFrame, or
:func:`bibliography_io.get_nr_records` to count records without loading the
full result into a DataFrame.

.. code-block:: python

   from pathlib import Path

   from bibliography_io import get_nr_records, load_df

   filename = Path("references.csv")
   count = get_nr_records(filename)
   records_df = load_df(filename)

Optional dependencies
---------------------

The package's public loading and writing functions require CoLRev. Install it
with ``python -m pip install "bibliography-io[colrev]"``. The ``requests`` extra
is available separately for optional request-related functionality.
