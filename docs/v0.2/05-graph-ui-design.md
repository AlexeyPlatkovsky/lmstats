# v0.2 Stage 5 — Minimal Historical Graph UI Specification

Inputs: `AGENTS.md`, `docs/v0.2/02-baseline.md`, `docs/v0.2/04-history-api-design.md`. No product UI change is made in this stage; this document fully specifies the v0.2 UI extension.

All changes stay inside `static/index.html` (inline CSS + JS), consistent with the v0.1 single-file frontend. No framework, no new assets, no build step.

## 1. Placement

The existing v0.1 layout is preserved exactly (header, hero speed, model line, metrics table). One new section is inserted **below the metrics table and above the footer**, inside the same `.panel`:

```
Generation Speed History        ← section label (12px, letter-spaced, --dim; same style family as h1)
[ 5m ] [ 1h ] [ 24h ]           ← range buttons, left-aligned row
<svg graph>                     ← full panel width, ~200px tall
legend row                      ← compact, below the graph
```

The hero speed remains visually dominant; the graph is secondary. No other element moves, resizes, or restyles.

## 2. Range selector

- Three buttons: `5m`, `1h`, `24h`. Small, monochrome (border `--line`, text `--dim`); the active button uses `--accent` border + text and carries `aria-pressed="true"`.
- Default active: **1h**. On page load the UI fetches `/api/history?range=1h` once.
- Clicking a button: set it active (others inactive), fetch the new range, re-render the graph. **No page reload.**
- During a request: keep the previously rendered data; dim the graph area (opacity ~0.5) as a loading cue. Buttons stay enabled.
- Stale-response guard: each fetch carries an incrementing sequence number; a response that arrives after a newer request was started is ignored.
- On fetch failure (non-2xx or network error): show the text `History unavailable` centered in the graph area (dim color); keep the last good data hidden; buttons remain usable so the user can retry. A subsequent success restores the graph.

## 3. Graph

Plain **SVG** (no canvas, no library), one `<svg>` with a fixed `viewBox` and CSS `width: 100%` so it scales with the panel.

- X axis = time, spanning the full selected window: from `generatedAt − duration(range)` to `generatedAt` (durations per stage 4 §2). Points sit at their true time position, so sparse data is not stretched.
- Y axis = tokens/sec, from 0 to `1.1 × max(avgTokensPerSecond)` over all points (headroom); a flat zero line when the only value is 0.
- One `<path>` (polyline) per model series, one small `<circle>` per point as the hover target.
- Minimal axes: 4–5 dim time tick labels (HH:MM, local) and 3–4 speed tick labels; no gridline clutter.
- Points with `avgTokensPerSecond: null` are drawn on the axis (y = 0) but excluded from the Y-scale maximum.

## 4. Colors

Deterministic per model, stable across refreshes: palette slot = `djb2(modelName) % palette.length`.

| slot | color | note |
| --- | --- | --- |
| 0 | `#3fb950` | existing accent green |
| 1 | `#58a6ff` | blue |
| 2 | `#d29922` | existing warn amber |
| 3 | `#bc8cff` | purple |
| 4 | `#f778ba` | pink |
| 5 | `#39c5cf` | cyan |

All six are legible on the current `--bg: #0b0e14` dark theme and distinguishable from each other. A NULL model always uses `--dim` (`#8b949e`) and is labeled `unknown`. More than six models wrap around the palette (acceptable for a local tool; documented limitation).

## 5. Legend

One compact row below the graph, in series order: a small color swatch + model name (truncated with ellipsis if long), `--dim` text. NULL model shows as `unknown`.

## 6. Empty state

When the response has no series (stage 4 §5), render centered dim text in the graph area:

```
No generations recorded in this period.
```

No axes, no legend. Switching ranges re-evaluates the state per range.

## 7. Live update behavior

The existing SSE handler keeps updating hero/metrics exactly as in v0.1. Additionally:

- On each SSE message whose `prediction` is non-null, refresh the **currently selected** history range via `fetchHistory(currentRange)`.
- Dedupe: keep the last refreshed `prediction.timestampMs`; ignore messages whose timestamp equals it (the connect-time snapshot re-sends the latest prediction and must not double-fetch).
- Coalescing: if a fetch is already in flight when a refresh is requested, set a `pendingRefresh` flag; when the in-flight fetch completes, fire exactly one follow-up if the flag is set. This bounds refreshes to at most one per new prediction plus user clicks — no timers, no polling.
- The refresh re-renders only the graph/legend; hero and metrics are untouched by it.

## 8. Tooltip (lightweight)

One shared absolutely-positioned `<div>` (hidden by default). Hovering a point circle shows, near the cursor:

```
10:31:00            ← bucket start, local time (from the point timestamp)
qwen3.8-27b-mlx     ← model (or "unknown")
15.8 tok/s · 3 reqs ← avgTokensPerSecond (or "no speed data") + count
```

Mouse leave hides it. No libraries, no zoom/pan. (Included because it is simple; if implementation proves it complicates the graph code, it may be dropped — everything else stands.)

## 9. Browser verification checklist (Playwright)

Run against `http://127.0.0.1:8765` with the app started using `LM_SPEED_VIEWER_DB` pointed at a prepared temporary database (stage 3 §1 override) so tests never touch the production DB:

1. **Hero regression** — `#speed` visible; metrics table rows (TTFT/prompt/output/total/generation time) present and unchanged.
2. **Default range** — `1h` button carries the active state on load; a request to `/api/history?range=1h` was made.
3. **Range switching** — clicking `5m` / `24h` moves the active state and issues `/api/history?range=5m|24h`; no page reload.
4. **Graph renders** — with a seeded DB, the SVG contains one path per model and circles for points.
5. **Empty state** — with an empty DB, the exact text `No generations recorded in this period.` is shown.
6. **Multiple series distinguishable** — two seeded models produce two paths with different stroke colors; legend lists both.
7. **Live refresh** — on SSE connect (snapshot contains the seeded latest prediction), a `/api/history` fetch fires and the graph re-renders.
8. **Console** — no page errors / console errors during the above.

## Constraints honored

No custom dates, statistics table, extra KPI cards, zoom/pan, export, response history, or settings — the v0.2 UI adds exactly one section: label + range buttons + graph + legend (+ tooltip).

## Verification (this stage)

No product code changed; repository health re-confirmed for this stage: `ruff check .` PASS, `pytest` 22 passed, coverage ≥ 95% gate PASS. No browser change was made in this stage, so no Playwright run is required until implementation (stage 8).
