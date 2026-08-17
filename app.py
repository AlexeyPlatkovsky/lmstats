#!/usr/bin/env python3
"""Compatibility launcher for LM Stats Viewer.

Run: ``python app.py`` -> http://127.0.0.1:8765
"""

from lmstats import database as db
from lmstats.application import STATIC_DIR, create_app, parse_utc, utcnow
from lmstats.collector import Collector, LMS_CANDIDATES
from lmstats.parser import PREDICTION_TYPE, parse_line

__all__ = [
    "Collector", "HOST", "LMS_CANDIDATES", "PORT", "PREDICTION_TYPE", "STATIC_DIR",
    "api_dashboard", "api_history", "api_state", "app", "collector", "create_app", "db",
    "events", "index", "lifespan", "parse_line", "_parse_utc", "_utcnow",
]


HOST = "127.0.0.1"
PORT = 8765

collector = Collector()
app = create_app(collector=collector)

# Compatibility names retained for existing integrations and tests.
_utcnow = utcnow
_parse_utc = parse_utc
index = app.state.index_handler
api_state = app.state.api_state_handler
api_history = app.state.api_history_handler
api_dashboard = app.state.api_dashboard_handler
events = app.state.events_handler
lifespan = app.router.lifespan_context


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT, log_level="warning", timeout_graceful_shutdown=5)
