# LM Speed Viewer v0.2

A tiny local web app that shows the statistics of the **latest completed**
LM Studio generation, with generation speed (tok/s) as the primary metric,
plus a historical graph of past generations.

It is a passive observer: it runs the `lms` CLI log stream as a child process
and displays whatever LM Studio logs. It does not proxy, restart, or configure
LM Studio in any way.

## What it shows

- Generation speed (tok/s) — the dominant element
- Model identifier
- Time to first token (TTFT)
- Prompt / output / total token counts
- Generation time
- Collector status (Connected / Disconnected / Error / Waiting for first prediction)
- Historical speed graph (5m / 15m / 1h / 24h ranges, plus the last ten values
  per model from the past month; stored in SQLite)
- Clickable model legend for filtering and hover comparison
- The eight most recent generations, regardless of the selected graph range

## Requirements

- Python 3.10+
- LM Studio installed and running, with the `lms` CLI on your PATH
  (or at `~/.lmstudio/bin/lms`)

## Install

For a standalone command available from any directory, install with
[pipx](https://pipx.pypa.io/):

```sh
pipx install .
```

`pipx` creates and manages an isolated virtual environment for the command; do
not commit a project `.venv`.

For development, create a local environment if desired and install the project
in editable mode:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -e . -r requirements-dev.txt
```

## Run

```sh
lm-speed-viewer
```

Optional configuration:

```sh
lm-speed-viewer --host 127.0.0.1 --port 8765 --db /tmp/speed-history.db
```

The compatibility launcher remains available:

```sh
python app.py
```

Then open: **http://127.0.0.1:8765**

## History persistence

v0.2 adds local storage of all completed predictions to a SQLite database
located at `~/.lmstudio-speed-viewer/history.db` by default. The graph UI
reads from this database via the dashboard and history endpoints.

### Override location

Set the `LM_SPEED_VIEWER_DB` environment variable to use a different path:

```sh
LM_SPEED_VIEWER_DB=/tmp/speed-history.db python app.py
```

### Limitations

- Only the **latest** generation is shown in the hero view.
- Internal/housekeeping LM Studio requests (e.g. title generation) are not
  classified and may temporarily become the latest prediction.
- The history graph stores predictions locally; clearing the SQLite file
  removes all historical data.
- More than six models use calculated shades of the six base graph colors.
