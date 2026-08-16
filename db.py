"""Compatibility alias for :mod:`lm_speed_viewer.database`."""

import sys

from lm_speed_viewer import database as _database


sys.modules[__name__] = _database
