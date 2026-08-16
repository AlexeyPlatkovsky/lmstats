# Testing Pyramid

LM Speed Viewer keeps backend coverage in pytest and executes the shipped
frontend in Chromium through `pytest-playwright`.  Tests never start, stop, or
configure LM Studio or `lms`.

## Backend

Parser, collector, persistence, history, and API tests use temporary SQLite
paths and mocked subprocess boundaries.  The coverage gate measures `app.py`
and `db.py`:

```sh
pytest --cov=app --cov=db --cov-report=term-missing --cov-fail-under=95
```

## Browser UI

`tests/test_browser_ui.py` serves the actual `static/index.html` from a small
local HTTP server.  It replaces translated-Python frontend tests and
HTML-string marker checks, which could pass without executing the JavaScript
shipped to users.

The tests stub only browser requests:

- `/api/dashboard` 404 plus `/api/history` validates legacy-server fallback,
  truthful unavailable-detail messaging, and fixed-range historical navigation.
- SVG labels, tooltip bounds, and `ResizeObserver` rendering run in Chromium.
- A narrow viewport validates that the Recent table can scroll horizontally;
  the same test verifies collector detail and seconds formatting in the real
  DOM.

Run the browser suite directly with:

```sh
pytest -m browser
```

## Manual acceptance

For a release check, use `playwright-cli` against `http://127.0.0.1:8765` to
inspect desktop and narrow viewports, live SSE updates, tooltips, and console
output.  This is observational only and must not control LM Studio or `lms`.
