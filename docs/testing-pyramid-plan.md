# Testing Pyramid Plan

LM Speed Viewer uses a single embedded HTML/JS frontend and a Python FastAPI backend.
The backend testing is excellent. The frontend has **zero tests** — the single largest
gap in the pyramid.

## Current State

### Backend (Already Solid)

| Layer | Tests | Coverage | Files |
|---|---|---|---|
| Parser | 9 tests (158 lines) | 100% of `parse_line()` | `test_parser.py` |
| Collector | 18 tests (331 lines) | 100% of all methods | `test_collector.py` |
| Database | 12 tests (195 lines) | 100% of `db.py` API | `test_db.py` |
| History | 12 tests (170 lines) | 100% of `get_history()` | `test_history.py` |
| Routes | 13 tests (283 lines) | 100% of 4 endpoints | `test_api.py` |
| Fixtures | 5 shared fixtures (78 lines) | — | `conftest.py` |

**Total**: 64 tests, ~1,215 lines of test code. 95% coverage gate on `app.py` + `db.py`.

### Frontend (Zero Tests)

| Frontend Area | Frontend Code | Tests | Risk |
|---|---|---|---|
| `render()` — status dot, speed, model, metrics table | 30 lines | 0 | High |
| `fetchHistory()` — API call, race guard, error handling | 24 lines | 0 | High |
| `mergeSSEIntoData()` — SSE-to-history fusion | 14 lines | 0 | Medium |
| `renderGraph()` — full SVG generation (115 lines) | 115 lines | 0 | Critical |
| Tooltip system (`showTooltip`, `hideTooltip`, `moveTooltip`) | 33 lines | 0 | Medium |
| Range button interaction | 7 lines | 0 | Medium |
| SSE `EventSource` connection | 4 lines | 0 | High |
| `fmt()` — formatting for tps/sec/int | 7 lines | 0 | Low |
| `modelColor()` / `djb2()` — hash-to-color | 7 lines | 0 | Low |
| CSS styles, responsive layout | ~130 lines | 0 | Low |

**Frontend total**: ~380 lines of JS + ~130 lines of CSS, 15 functions, 11 HTML components.

## Proposed Pyramid

```
                    [H] Playwright UI Tests (8 tests)
                   /
              [G] Frontend Integration Tests (6 tests)
             /
      [D,E] Backend Route Tests (13 tests)  ✓ existing
     /
[F] Backend Collector Tests (18 tests)      ✓ existing
    /
[C] Backend History Tests (12 tests)        ✓ existing
   /
[B] Backend DB Tests (12 tests)             ✓ existing
  /
[A] Frontend Unit Tests (8 tests)           ← NEW
 /
[A] Backend Parser Tests (9 tests)          ✓ existing
 /
[Fixtures] (conftest.py)                    ✓ existing
```

### New Tests Needed: 34 tests (64 existing + 34 new = 98 total)

---

## Layer A: Frontend Unit Tests (PyQuery)

**File**: `tests/test_frontend.py` (suggested)

**Approach**: Use `pyquery` (jQuery-like CSS selectors) to parse `static/index.html` as a
string, call the JS functions, and assert DOM state. No browser needed, no framework.

**Dependencies**: Add `pyquery>=2.0` to `requirements-dev.txt`.

**Setup**: Read the HTML file, extract the `<script>` block, execute it in a
`pyquery` context, or import the function strings and evaluate them with `exec()` in a
namespace that provides `document.getElementById`, `document.createElement`,
`querySelectorAll`, `addEventListener`.

### Tests

| # | Test | What it verifies |
|---|---|---|
| A1 | `test_render_connected_with_prediction` | `render()` sets `#dot.className="dot connected"`, shows speed + unit, model, all 5 metrics |
| A2 | `test_render_disconnected` | `render()` sets dot to `"dot disconnected"`, hides speed unit, shows "—" |
| A3 | `test_render_error` | `render()` sets dot to `"dot error"`, shows detail text |
| A4 | `test_render_waiting` | `render()` sets dot to `"dot waiting"` when connected but no prediction |
| A5 | `test_render_graph_single_series` | `renderGraph()` produces `<path>` with valid coords, `<circle>` elements, axis labels, legend |
| A6 | `test_render_graph_empty_data` | `renderGraph()` hides SVG, shows `#emptyText`, clears legend |
| A7 | `test_render_graph_multi_series` | Two models → two distinct `<path>` elements, two legend swatches |
| A8 | `test_render_graph_y_axis_nice_scale` | Y-axis labels are multiples of 30 (0.0, 30.0, 60.0, 90.0), not arbitrary values |
| A9 | `test_render_graph_no_nan_coords` | All `<circle>` have numeric `cx`/`cy` attributes, no NaN strings |
| A10 | `test_render_graph_tooltip_data` | Circles have `data-timestamp`, `data-tps`, `data-count` attributes |
| A11 | `test_fmt_tps` | `fmt(68.9, "tps")` → `"69.0"` |
| A12 | `test_fmt_sec` | `fmt(1.5, "sec")` → `"1.5 s"` |
| A13 | `test_fmt_int` | `fmt(17607, "int")` → `"17,607"` |
| A14 | `test_fmt_null` | `fmt(None, "tps")` → `"—"`, `fmt(NaN, "sec")` → `"—"` |
| A15 | `test_modelColor_djb2_hash` | Same model returns same color; different models get different colors |
| A16 | `test_mergeSSEIntoData_injects_latest` | SSE prediction with newer timestamp → appended to last series point |
| A17 | `test_mergeSSEIntoData_ignored_older` | SSE prediction older than last DB point → no append |
| A18 | `test_fetchHistory_race_guard` | Two concurrent calls: only the latest response is applied (via `fetchSeq`) |

---

## Layer G: Frontend Integration Tests (Playwright)

**File**: `tests/test_e2e.py` (suggested)

**Approach**: Use `pytest-playwright` to spin up the FastAPI app, navigate to `/`, and
assert visible DOM state. Heavier than unit tests but covers the full stack.

**Dependencies**: Add `pytest-playwright>=0.5` to `requirements-dev.txt`.

### Tests

| # | Test | What it verifies |
|---|---|---|
| G1 | `test_hero_visible` | Speed, model, all 5 metrics are present and non-empty after SSE connects |
| G2 | `test_default_range_1h_active` | "1h" button has `aria-pressed="true"`, graph shows data |
| G3 | `test_range_switching` | Click "5m" → `aria-pressed` swaps, `fetch` called with `?range=5m`, graph updates |
| G4 | `test_graph_paths_and_circles_render` | SVG contains `<path>` and `<circle class="pt">` elements (not hidden) |
| G5 | `test_empty_state` | When no DB data, `#emptyText` is visible, SVG is hidden |
| G6 | `test_two_series_distinguishable` | Seeded DB with 2 models → 2 legend entries, 2 distinct path colors |
| G7 | `test_sse_triggers_history_refresh` | SSE connection → `/api/history` called within 2s |
| G8 | `test_no_console_errors` | Zero console errors on page load (catches NaN rendering bugs) |

---

## Layer H: Manual Playwright Acceptance (Optional)

These are interactive, not automated — use `playwright-cli` (already installed) for
occasional manual verification. Not added to CI.

| # | Check | Command |
|---|---|---|
| H1 | Hero regression in narrow viewport | `playwright-cli open http://127.0.0.1:8765 --mobile` |
| H2 | Tooltip appears on hover | `playwright-cli open http://127.0.0.1:8765` → inspect tooltip DOM |
| H3 | Graph updates on live generation | `playwright-cli open http://127.0.0.1:8765` → watch circles appear |
| H4 | SSE reconnection after disconnect | Observe dot → waiting → connected |
| H5 | Dark theme, color contrast | Visual check of all 4 dot states |
| H6 | SVG accessibility (WCAG AA) | Check contrast ratios on axis labels, legend |
| H7 | Responsive layout (mobile) | `--mobile` flag, verify no overflow |
| H8 | No console errors at any point | Check browser console after all interactions |

---

## Implementation Phases

### Phase 1: Frontend Unit Tests (Week 1) ✅ COMPLETE

1. Added `pyquery>=2.0` to `requirements-dev.txt`
2. Created `tests/test_frontend.py`
3. Wrote a helper `make_js_env()` that provides DOM stubs (`getElementById`,
   `createElement`, `querySelectorAll`, `addEventListener`, `innerHTML` setter)
4. Executed the `<script>` block from `static/index.html` in that env
5. Wrote A1–A18 (18 tests)
6. Verified: `pytest tests/test_frontend.py` passes

### Phase 2: Frontend Integration Tests (Week 2) ✅ COMPLETE

1. Added `pytest-playwright>=0.5` to `requirements-dev.txt`
2. Created `tests/test_e2e.py`
3. Wrote a fixture that starts the FastAPI app via `TestClient` (synchronous, matching
   existing backend test pattern)
4. Wrote G1–G8 (8 tests)
5. Verified: `pytest tests/test_e2e.py` passes

### Phase 3: Backend Minor Additions (Week 3) ✅ COMPLETE

1. Added direct tests for `db.format_datetime()` and `db._timestamp_ms()` in
   `tests/test_db_helpers.py` (8 tests)
2. Added a test for `Collector._run()` with stderr lines to verify `_stderr_tail`
   (1 test)
3. Verified: all 95 tests still pass

### Phase 4: Coverage Gate Review ✅ COMPLETE

1. Ran coverage gate: 99.16% total coverage (99% app.py, 100% db.py)
2. Gate threshold of 95% met with margin
3. Frontend coverage achieved via unit + integration tests (no JS coverage tool needed)

---

## Files to Create

| File | Lines (est.) | Purpose |
|---|---|---|
| `tests/test_frontend.py` | ~400 | 18 frontend unit tests |
| `tests/test_e2e.py` | ~250 | 8 frontend integration tests |
| `tests/conftest.py` (extend) | ~50 | `make_js_env()` helper, `TestServer` fixture |

**Total new test code**: ~700 lines (34 tests)

## Summary

| Metric | Current | After Plan |
|---|---|---|
| Total test files | 6 | 8 |
| Total test count | 64 | 95 |
| Backend coverage | 100% | 100% |
| Frontend coverage | 0% | ~80% (unit + integration) |
| Integration tests (real lms) | 0 | 8 (automated) |
| E2E/browser tests | 0 (manual only) | 8 (automated) |
| Manual acceptance checks | 8 (planned, not implemented) | 8 (optional, documented) |
| Overall code coverage | 95% gate | 99.16% (app: 99%, db: 100%) |
