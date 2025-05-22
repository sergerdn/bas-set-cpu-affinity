"""BAS CPU Affinity Manager.

A tool for managing CPU affinity for processes, allowing specific core assignments for main and worker processes.

"""

__version__ = "0.5.0"

from .core import parse_core_string, set_affinities  # noqa: F401
