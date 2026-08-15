# v0.2 Stage 2 — Baseline Audit and Current Architecture Map (v0.1)

Audited: 2026-08-15 · branch `feature/lms-2-v0.2-planning` from `main` @ de61d1c

## Baseline status

Healthy. Verified on this branch:

- `ruff check .` — PASS
- `pytest` — 22 passed (parser 4, collector 15, api/SSE 3)
- `pytest --cov=app --cov-fail-under=95` — 98.56% (only the `__main__` block, app.py:211-213, uncovered)

No code changes were required to restore the baseline. No v0.2 feature was added in this stage, per the task brief. The app itself did not need to be started; behavior is fully covered by the test suite and code inspection.

## Project structure

```
app.py               # entire backend: parser, collector, FastAPI app, SSE (213 lines)
static/index.html    # entire frontend: single page with inline CSS + JS
tests/
  test_parser.py     # parse_line unit tests (4)
  test_collector.py  # Collector lifecycle + pub/sub via FakeProc/FakeStream (15)
  test_api.py        # routes + SSE stream via TestClient / direct coroutine (3)
tasks/               # v0.2 stage briefs (01-08)
.claude/             # agent skills, pipelines, reviewer prompt
.taskpilot/          # task workspace (LMS-*)
requirements.txt     # fastapi, uvicorn
requirements-dev.txt # + pytest, pytest-cov, ruff, httpx2
pyproject.toml       # ruff (E,F; line-length 100), pytest pythonpath=["."]
```

Single-file backend by design; no package, no ORM, no frontend framework.

## Data flow: `lms log stream` → browser

1. FastAPI lifespan (app.py:167-171) calls `collector.start()` on startup.
2. `Collector.start()` (app.py:99) resolves the lms binary (`LMS_CANDIDATES`: PATH, then `~/.lmstudio/bin/lms`), spawns `lms log stream --source model --filter output --stats --json` via `asyncio.create_subprocess_exec`, sets status `connected`, and launches the `_run()` task.
3. `_run()` (app.py:123) reads stdout line by line; every line goes through `parse_line()` (app.py:29).
4. `parse_line` returns a normalized dict only for `data.type == "llm.prediction.output"` events; malformed JSON, non-dict payloads, and unrelated event types yield `None` (silently ignored).
5. A valid prediction replaces `collector.prediction` (latest only, in memory) and triggers `publish()`.
6. `publish()` (app.py:91) pushes the JSON snapshot to every SSE subscriber queue (`asyncio.Queue(maxsize=100)`); a full queue drops the update — slow clients rely on EventSource auto-reconnect.
7. Browser: `static/index.html` opens `EventSource("/events")`; the first message is the current snapshot, then queued updates; a 15 s keepalive comment (`: keepalive`) is sent when the queue is empty. `render()` updates the DOM; on error, EventSource reconnects automatically.
8. On shutdown, lifespan calls `collector.stop()`: sets `_stopping`, terminates its own child (5 s grace, then kill).

## Current prediction fields (normalized)

| Field | Source in lms event | Notes |
| --- | --- | --- |
| `modelIdentifier` | `data.modelIdentifier` | str, or None (empty string → None) |
| `tokensPerSecond` | `stats.tokensPerSecond` | number or None; the primary metric |
| `timeToFirstTokenSec` | `stats.timeToFirstTokenSec` | number or None |
| `totalTimeSec` | `stats.totalTimeSec` | number or None |
| `promptTokensCount` | `stats.promptTokensCount` | number or None; booleans rejected |
| `predictedTokensCount` | `stats.predictedTokensCount` | number or None (output tokens) |
| `totalTokensCount` | `stats.totalTokensCount` | number or None |
| `timestampMs` | top-level `timestamp` | epoch milliseconds, or None; booleans rejected |

Real events also carry `stats.stopReason` and the output text (see `REAL_EVENT` in tests/test_parser.py:13); v0.1 discards both — the v0.2 design decides whether to keep them.

## Key responsibilities

- `parse_line(line)` — pure function; one lms JSON line → normalized dict or None.
- `Collector` — subprocess lifecycle (start/_run/stop), stderr tail (last 5 lines; captured but not exposed by any route), status state machine (`starting | connected | disconnected | error` + `detail`), latest prediction, SSE pub/sub.
- `lifespan` — starts/stops the collector with the app.
- Routes: `/` serves `static/index.html`; `GET /api/state` returns the snapshot (polling fallback); `GET /events` is the SSE stream.
- Frontend — hero speed + model line, metrics table (TTFT / prompt / output / total / generation time), status dot + text, last-update clock; everything is driven by SSE messages.

## Existing tests and gaps

Covered: parser (valid / malformed / unrelated / missing fields), collector lifecycle with fakes (spawn failure, EOF → disconnected, stop paths incl. kill-on-timeout, stderr tail), API routes + SSE stream (initial snapshot, queued update, keepalive, subscriber cleanup).

Gaps relevant to v0.2:

- No persistence of any kind — `collector.prediction` is lost on restart (documented v0.1 limitation).
- No history of any kind — each prediction replaces the previous one; nothing is stored or ordered.
- `stopReason` arrives in real events but the parser drops it (v0.2 may retain it).
- The SSE slow-client drop is tested at queue level only, not end-to-end.

## Likely extension points for persistence/history

1. **Insertion point:** `Collector._run()` where `self.prediction = pred` happens (app.py:132) — the single choke point every valid prediction passes; persistence, latest-state update, and publish can be sequenced here.
2. **Startup:** `lifespan` (app.py:167) — natural place to initialize the DB schema idempotently and load the latest stored prediction before `collector.start()`.
3. **Snapshot:** `Collector.snapshot()` (app.py:84) defines the `/api/state` and SSE payload shape; a history endpoint can be added as a new route without touching it.
4. **Frontend:** `render()` in index.html — a graph section can be added below the metrics table; SSE messages already trigger re-render.
5. **Time:** `timestampMs` (epoch ms) is the only time source; v0.2 should normalize to UTC at parse/persist time rather than trusting the browser clock.

## Risks later stages must preserve (v0.2 regression requirements)

UI behavior that must remain unchanged:

- latest generation only in the hero; speed (tok/s) stays visually dominant
- model identifier line
- TTFT, prompt / output / total tokens, generation time rows
- collector status dot + text (Connected / Waiting for first prediction / Disconnected / Error)
- automatic live updates via SSE; EventSource reconnect behavior

Engineering invariants:

- passive observation only — never proxy, restart, kill, or configure LM Studio; the app spawns and reads `lms log stream` only
- malformed / unrelated lines must remain safely ignored (parser contract)
- slow SSE clients drop updates without blocking the collector (`QueueFull` → drop)
- shutdown terminates only its own child process (5 s grace, then kill)
- tests must not spawn a real lms (tests monkeypatch `LMS_CANDIDATES` / `create_subprocess_exec`)
- single-file backend + single-file frontend; keep new code small and local

## Blockers discovered

None. Baseline is green (lint / tests / coverage above).
