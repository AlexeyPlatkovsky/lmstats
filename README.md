# LM Stats Viewer

> **See how fast your local LLM is running—at the moment it matters.**
>
> LM Stats Viewer turns LM Studio generation logs into a focused live dashboard:
> speed first, context close behind, and history when you want to compare.

[![License](https://shields.io/badge/license-Apache%202-blue)](LICENSE) [![npm version](https://img.shields.io/npm/v/lmstats)](https://www.npmjs.com/package/lmstats)

**⚡ Live tok/s** &nbsp; **📈 Built-in history** &nbsp; **🔒 Passive and local**

![LM Stats Viewer dashboard showing generation speed, recent generations, and model history](docs/README.png)

## Make every generation easier to read

LM Stats Viewer is a tiny local web app for the **latest completed** LM Studio
generation. It puts generation speed (tok/s) front and centre, adds the
latency and token details that explain it, and keeps a historical graph of past
generations.

It is a passive observer: it runs the `lms` CLI log stream as a child process
and displays what LM Studio logs. It does not proxy, restart, or configure
LM Studio in any way.

## Highlights

- ⚡ **Speed, first.** See the latest completed generation's tok/s without
  digging through logs.
- ⏱ **Context at a glance.** Check the model, time to first token (TTFT),
  prompt/output/total token counts, and generation time together.
- 📈 **History that stays useful.** Explore 5m, 15m, 1h, and 24h views, or the
  past month's last ten values per model—stored locally in SQLite.
- 🧭 **Compare models clearly.** Filter the graph from its clickable legend and
  compare values on hover.
- 🗂 **Recent runs, ready when needed.** Review the eight newest generations,
  independent of the graph's selected range.
- 🟢 **Know the collector state.** The dashboard labels Connected,
  Disconnected, Error, or Waiting for first prediction.

## Requirements

- Python 3.10+
- LM Studio installed and running, with the `lms` CLI on your PATH
  (or at `~/.lmstudio/bin/lms`)

## Install

For a standalone command available from any directory, install with
[npm](https://www.npmjs.com/package/lmstats):

```sh
npm install -g lmstats
```
Run

```sh
lmstats
```

Then open:
```
**http://127.0.0.1:8765**
```

## Development
For development, create a local environment if desired and install the project
in editable mode:

```sh
git clone https://github.com/AlexeyPlatkovsky/lmstats.git
cd lmstats
python -m venv .venv
source .venv/bin/activate
pip install -e . -r requirements-dev.txt
```

## Run

Optional configuration:

```sh
lmstats --host 127.0.0.1 --port 8765 --db /tmp/speed-history.db
```


## History persistence

The viewer stores all completed predictions in a local SQLite database
located at `~/.lmstats/history.db` by default. The graph UI
reads from this database via the dashboard and history endpoints.


### Limitations

- Only the **latest** generation is shown in the hero view.
- Internal/housekeeping LM Studio requests (e.g. title generation) are not
  classified and may temporarily become the latest prediction.
- The history graph stores predictions locally; clearing the SQLite file
  removes all historical data.
- Predictions reporting 0 or more than 999 tok/s are ignored as implausible log outliers.

## FAQ

### Does it control LM Studio or send my prompts anywhere?

No. The viewer passively reads LM Studio's output log stream. It does not
proxy requests, restart LM Studio, or change its configuration.

### Where is the history stored?

Completed predictions are stored locally in SQLite at
`~/.lmstats/history.db` by default. Use `--db` or the
`LMSTATS_DB` environment variable to choose another location.

### Why is the dashboard waiting for a prediction?

The viewer has not yet received a completed generation from the LM Studio log
stream. Run a generation, then refresh the dashboard if needed.

### Can I clear the history?

Yes. Stop the viewer and remove its SQLite database file, or point the viewer
at a new database with `--db` or `LMSTATS_DB`.

### Why might a generation not appear on the graph?

The hero view shows only the latest completed generation. The graph stores
completed predictions, except implausible log outliers above 999 tok/s; some
internal LM Studio requests can also temporarily become the latest prediction.
