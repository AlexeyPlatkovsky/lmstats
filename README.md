# LM Speed Viewer v0.1

A tiny local web app that shows the statistics of the **latest completed**
LM Studio generation, with generation speed (tok/s) as the primary metric.

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

## Telemetry source

The app launches and continuously reads:

```sh
lms log stream --source model --filter output --stats --json
```

Malformed or unrelated lines are ignored safely. Only the latest valid
completed prediction is kept in memory; each new one replaces it and pushes an
update to open browser tabs over SSE (browsers reconnect automatically).

## Limitations (v0.1)

- Only the **latest** generation is shown. History is intentionally not stored;
  after an app restart the page shows "Waiting for first prediction" until a
  new generation completes.
- Internal/housekeeping LM Studio requests (e.g. title generation) are not
  classified and may temporarily become the latest prediction.
