# v0.2 Stage 7 — Implementation Plan and Release Checklist

Inputs: `AGENTS.md`, `docs/v0.2/02-baseline.md` … `06-test-plan.md`, and the current repository. This is a planning document only — **no v0.2 code is written in this stage.** It converts the approved designs into one bounded, TDD-ordered plan for the final implementation stage (LMS-10 / `tasks/08-implement-v0.2.md`).

## 1. Files to create / change

| File | Action | Purpose |
| --- | --- | --- |
| `db.py` | **create** | SQLite storage layer: schema, path resolution, connect, timestamp format, insert, latest, `get_history` (stage 3 §8 + stage 4 §7). No ORM. |
| `app.py` | **change** | (a) parser gains `stopReason` + `output`; (b) `Collector` gains a `db_path` and persists each valid prediction (insert → latest state → publish, non-fatal on DB error); (c) lifespan resolves `db.default_db_path()` at startup, runs `init_db`, loads latest before `collector.start()`; (d) new route `GET /api/history`. |
| `static/index.html` | **change** | Add the history section (label + range buttons + SVG graph + legend + tooltip) per stage 5; keep hero/metrics untouched. |
| `tests/conftest.py` | **create** | Shared fixtures: `db_path`, `now`, `sample_prediction`, `sample_raw_event`, `seed` (stage 6). |
| `tests/test_db.py` | **create** | Group B. |
| `tests/test_history.py` | **create** | Group C. |
| `tests/test_parser.py` | **change** | Group A (new keys). |
| `tests/test_api.py` | **change** | Groups D, E (extend existing fixtures). |
| `tests/test_collector.py` | **change** | Group F (extend existing fakes). |
| `AGENTS.md` | **change** | Widen the coverage gate command to `--cov=app --cov=db` (stage 6 Coverage). |
| `README.md` | **change** | Document v0.2: history persistence, `/api/history`, the graph UI, DB location + `LM_SPEED_VIEWER_DB` override; update the "Limitations" section (history now survives restart). |

No new dependencies. No frontend framework. No package restructuring — `db.py` sits beside `app.py`.

## 2. Exact implementation order (TDD)

Each "add tests" step must be written to fail first, then made green by the following implementation step. Run focused checks after each pair; run the full gate at the marked barriers.

```
 1. add conftest fixtures + Group B (test_db.py)            [red]
 2. implement db.py core: SCHEMA, default_db_path, init_db, connect,
    format_timestamp, insert_prediction, latest_prediction, row_to_prediction   [green]
 3. run: pytest tests/test_db.py + ruff check .
 4. add Group C (test_history.py)                           [red]
 5. implement db.get_history + RANGE_DURATIONS/BUCKET_SIZES [green]
 6. run: pytest tests/test_db.py tests/test_history.py + coverage (db)
 7. add Group D history-API tests (test_api.py)             [red]
 8. implement GET /api/history route + parser stopReason/output   [green]
 9. run: pytest tests/test_api.py + ruff check .
10. add Group E startup tests (dedicated seeded fixture)    [red]
11. implement lifespan wiring: resolve path, init_db, load latest before start   [green]
12. add Group F collector write-path tests (test_collector.py)   [red]
13. implement Collector persistence: db_path, insert→state→publish, non-fatal error   [green]
14. BARRIER — full regression: ruff check . + pytest (all) + coverage gate (app+db ≥95%)
15. implement graph UI in static/index.html (stage 5)       [no new Python]
16. run full automated checks again; update README.md + AGENTS.md docs
17. real LM Studio integration acceptance (Group G, manual) [release gate]
     — if the implementing agent itself runs through LM Studio, its own
       generation may serve as the real telemetry (tasks/08)
18. playwright-cli browser acceptance (Group H + the extra checks in tasks/08:
     page load, layout readability)                          [release gate]
19. code-reviewer fresh read-only pass → fix valid findings → rerun all release gates
```

Steps 15–16 change only the frontend and docs; they add no Python, so the coverage gate is unaffected but must still be rerun to confirm nothing regressed.

## 3. Scope boundaries (explicitly prohibited in v0.2)

- custom date picker / arbitrary ranges
- summary statistics table or extra KPI cards
- cache-ratio analytics
- internal/housekeeping request filtering or classification
- any additional analytics/aggregation tables in SQLite
- frontend framework, bundler, or build step
- schema migrations / migration tooling
- data export
- user settings / persistence of preferences
- broad refactors of the parser, collector, or existing routes

If a need for any of these appears during implementation, stop and return to the manager — do not expand scope inline.

## 4. Risk list (risk → test/gate)

| Risk | Mitigation / gate |
| --- | --- |
| Timestamp float drift or format mismatch breaking string comparison | `format_timestamp` uses integer-ms arithmetic (stage 3 §3); B.8 asserts exact ms + lexicographic order; C.4 boundary tests. |
| SQLite reader/writer lock errors (FastAPI reads + collector writes) | WAL set in `init_db`; one short-lived connection per operation (stage 3 §5); F.1 runs with an SSE subscriber attached to prove a write succeeds alongside a reader. |
| Duplicate inserts (same event stored twice) | One insert per valid line at the single `_run` choke point; F.2 asserts invalid/unrelated lines create zero rows; G verifies one real generation → exactly one row. |
| Multiple models mixed into one series | Group-by `(model, bucket)` in `get_history`; C.5 + D.5 assert separation; H.6 asserts two visually distinct series. |
| Long-range graph point count exploding | Bucketing bounds points to ≤96 per range (stage 4 §3); C.7 asserts absolute bucket alignment; no per-row points are emitted. |
| SSE refresh loops / stale responses | Stage 5 §7 dedupe (by `timestampMs`) + in-flight coalescing; H.7 asserts exactly one refresh on connect; H.8 asserts no console errors. |
| Regression of the v0.1 hero/current view | All existing parser/collector/api tests unchanged and green (step 14 barrier); H.1 asserts hero + metrics table intact; E.3 asserts a live event still replaces latest state. |
| Test data leaking into the production DB | Every test uses an explicit temp path; B.9 asserts env override resolution without opening the real file; conftest never calls `default_db_path()` for writes. |

## 5. Release checklist (all must be PASS)

```
Ruff: PASS
pytest: PASS
coverage >=95% (app + db): PASS
real LM Studio event persisted: PASS          (Group G)
restart persistence: PASS                     (Group G step 4-5)
history 5m/1h/24h: PASS                       (Group G + H)
default 1h: PASS                              (H.2)
multiple models separated: PASS               (H.6)
playwright-cli: PASS                          (Group H)
code-reviewer executed: PASS                  (step 19)
review findings addressed: PASS               (step 19)
final regression checks: PASS                 (ruff + pytest + coverage, post-fixes)
README updated: PASS                          (step 16)
```

## 6. Final-stage token discipline

The implementing agent must not redesign. It should:

- trust these documents (`02`–`07`) unless the code reality provably contradicts them; if it does, record the discrepancy and return to the manager rather than silently diverging.
- implement only the specified scope (§3); no opportunistic cleanup, renames, or abstractions.
- run focused checks incrementally (step 3/6/9) and the full gate only at barriers, to keep feedback fast.
- stop investigating unrelated issues (pre-existing warnings, style nits outside the diff) — note them and move on.
- use concise tool outputs (targeted `pytest <file>`, `git diff --stat`) rather than dumping whole files.

## Verification (this stage)

No product code changed; repository health re-confirmed for this stage: `ruff check .` PASS, `pytest` 22 passed, coverage ≥ 95% gate PASS.
