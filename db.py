"""Compatibility alias for :mod:`lmstats.database`."""

import sys

from lmstats import database as _database


sys.modules[__name__] = _database
