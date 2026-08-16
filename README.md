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
- Historical speed graph (5m / 1h / 24h ranges, stored in SQLite)

## Requirements

- Python 3.10+
- LM Studio installed and running, with the `lms` CLI on your PATH
  (or at `~/.lmstudio/bin/lms`)

## Install

```sh
pip install -r requirements.txt   # fastapi, uvicorn
```

## Run

```sh
python app.py
```

Then open: **http://127.0.0.1:8765**

## History persistence

v0.2 adds local storage of all completed predictions to a SQLite database
located at `~/.lmstudio-speed-viewer/history.db` by default. The graph UI
reads from this database via the `/api/history` endpoint.

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
- More than six models on the graph wrap around the color palette.
