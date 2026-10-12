"""Public interface for loading and writing bibliographic records."""

from .loader.load_utils import get_nr_records
from .loader.load_utils import load as load_records
from .loader.load_utils import load_df
from .loader.load_utils import loads
from .writer.write_utils import to_string
from .writer.write_utils import write_file as write_records

load = load_records
write = write_records
write_file = write_records

__all__ = [
    "get_nr_records",
    "load",
    "load_df",
    "load_records",
    "loads",
    "to_string",
    "write",
    "write_records",
    "write_file",
]
