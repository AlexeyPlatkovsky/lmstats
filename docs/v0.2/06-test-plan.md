# v0.2 Stage 6 — Test Plan and Fixtures

Inputs: `AGENTS.md`, `docs/v0.2/02-baseline.md` … `05-graph-ui-design.md`. No product code is implemented in this stage; this plan defines the exact tests added during implementation (stage 8) so it can proceed test-first.

## Test file layout

| File | Groups | Status |
| --- | --- | --- |
| `tests/test_parser.py` | A | extend existing |
| `tests/test_db.py` | B | new |
| `tests/test_history.py` | C | new |
| `tests/test_api.py` | D, E | extend existing |
| `tests/test_collector.py` | F | extend existing |
| (manual) | G | release-gate acceptance, not in pytest |
| (playwright-cli) | H | release-gate browser acceptance |

## Shared fixtures (`tests/conftest.py`, new)

- `db_path(tmp_path)` → `tmp_path / "history.db"`; every DB test uses it explicitly. Nothing in the suite may open `db.default_db_path()`.
- `now` → fixed UTC reference: `datetime(2026, 8, 15, 10, 30, 0, tzinfo=timezone.utc)`. All time-dependent logic receives `now` as a parameter; no test may read the real clock.
- `sample_prediction` → full normalized dict (values from the existing `REAL_EVENT`): `modelIdentifier "qwen3.8-27b-mlx"`, `tokensPerSecond 15.841340338684146`, `timeToFirstTokenSec 13.94`, `totalTimeSec 6.755`, `promptTokensCount 16632`, `predictedTokensCount 107`, `totalTokensCount 16739`, `timestampMs 1786744778242`, plus the new keys `stopReason "eosFound"`, `output "fixture output text"`.
- `sample_raw_event` → the existing `REAL_EVENT` JSON string (single line).
- `seed(db_path, prediction, *, ts_offset_s=0)` helper → inserts one row with the given prediction and a timestamp of `now + ts_offset_s` (formatted per stage 3 §3). Used to place rows at exact offsets for boundary/bucket tests.
- `client` (in `test_api.py`, extends the existing fixture) → additionally monkeypatches `db.default_db_path` to return a fresh temp path per test, so the app lifespan (init + latest load) runs against isolated storage. The app must resolve `db.default_db_path()` **at lifespan startup, not import time** (stage 8 wiring), so the monkeypatch takes effect when `TestClient` enters its context.

## A. Parser regression (`tests/test_parser.py`)

Existing four tests stay unchanged and must keep passing. Add:

1. `test_stop_reason_captured` — real event shape → `stopReason == "eosFound"`; missing/non-str `stats.stopReason` → None.
2. `test_output_captured` — `data.output` string → `output`; missing/non-str → None.
3. The existing valid/malformed/unrelated/missing-field tests assert per-key and keep passing unchanged; add the two new keys (`stopReason`, `output`) to the valid-event test's assertions only.

## B. SQLite layer (`tests/test_db.py`, new)

1. `test_init_creates_schema` — fresh path: table + both indexes exist (query `sqlite_master`); parent dir auto-created.
2. `test_init_idempotent` — `init_db` twice, and again after inserts: no error, data unchanged.
3. `test_insert_roundtrip` — full prediction + raw line → rowid returned; every column equals the input (timestamp formatted per §3).
4. `test_latest_returns_newest` — seed rows at −10 s, −5 s, 0 → latest is the 0 row; equal-timestamp tie broken by later `id`.
5. `test_latest_empty_db` — None.
6. `test_persistence_across_reopen` — insert, close all connections, reconnect → row and latest survive.
7. `test_null_optional_fields` — prediction with all stats/model None → NULLs stored, read back as None; still returned by latest.
8. `test_timestamp_format` — `format_timestamp`: exact ms precision (no float drift), fixed-width `Z` format, lexicographic order matches chronological; None input → valid "now" format (assert shape/monotonicity only, never an exact wall-clock value).
9. `test_default_path_override` — env `LM_SPEED_VIEWER_DB` set → `default_db_path()` returns it; unset → `~/.lmstudio-speed-viewer/history.db` (monkeypatch `expanduser`/env; never open the real file).
10. `test_insert_failure_isolated` — insert against a path whose parent is a read-only dir raises; the exception propagates from `insert_prediction` (the collector, not the DB layer, decides it is non-fatal — see F).

## C. History queries (`tests/test_history.py`, new)

All use `seed()` against the fixed `now` and call `db.get_history(path, range_key, now=now)`.

1. `test_range_5m` — rows at −4 min, −30 s, 0 returned; −6 min excluded.
2. `test_range_1h` — rows at −59 min, −1 s, 0 returned; −2 h excluded.
3. `test_range_24h` — rows at −23 h, 0 returned; −25 h excluded.
4. `test_boundary_inclusive` — row exactly at window start included; 1 ms earlier excluded; row exactly at `now` included.
5. `test_multiple_models_separated` — two models, overlapping times → two series; no point mixes models.
6. `test_bucket_average` — one bucket, speeds 10 and 20 → `avgTokensPerSecond == 15.0`, `count == 2`; rounding case 10 + 10.555 → 10.28.
7. `test_bucket_alignment` — a row at 10:30:45 with range 1h lands in the bucket starting 10:30:00 (absolute alignment, stage 4 §3).
8. `test_null_speed_excluded_from_average` — bucket with one NULL-speed row and one 20.0 row → avg 20.0, count 2; all-NULL bucket → `avgTokensPerSecond is None`, correct count.
9. `test_empty_db` — body `{"range": ..., "generatedAt": <now formatted>, "series": []}`.
10. `test_deterministic_ordering` — series sorted by model ascending with NULL-model last; points ascending within a series (assert exact list order).

## D. History API (`tests/test_api.py`, extend)

Via the `client` fixture (temp DB per test):

1. `test_history_default_range` — no query param → 200, body `range == "1h"`.
2. `test_history_5m` / `test_history_1h` / `test_history_24h` — each returns 200 with the matching `range` and seeded data.
3. `test_history_invalid_range` — `?range=10m` → 400 with the stage-4 §1 error body.
4. `test_history_empty` — empty DB → 200, `series == []`.
5. `test_history_multiple_models` — two seeded models → two series, correct per-model points (mirrors C.5 at the HTTP layer).

## E. Startup behavior (`tests/test_api.py`, extend)

These tests need the DB seeded **before** the app lifespan runs (lifespan loads latest on `TestClient` entry), so they use a dedicated fixture — not the shared `client` — that (1) monkeypatches `db.default_db_path` to a temp path, (2) seeds rows via `seed()`, then (3) enters the `TestClient` context.

1. `test_startup_loads_latest_from_db` — seed a temp DB with two predictions, point the app at it (fixture), enter `TestClient` context → `collector.prediction` equals the seeded latest **before** any live event; `/api/state` reflects it.
2. `test_startup_empty_db` — no rows → `collector.prediction is None`, status flow unchanged from v0.1.
3. `test_startup_then_live_event_replaces` — after (1), feed one valid line through the collector path → latest state is the new event and a DB row was appended.

## F. Collector write path (`tests/test_collector.py`, extend)

No real LM Studio: reuse the existing `FakeProc`/monkeypatch patterns.

1. `test_run_persists_prediction` — `FakeProc` stdout with one valid prediction line; collector pointed at a temp DB → after `_run()`: exactly one DB row (values match), `collector.prediction` updated, subscriber queue received the snapshot.
2. `test_run_ignores_invalid_lines_for_db` — malformed + unrelated lines → zero rows, no state change (v0.1 behavior preserved).
3. `test_db_failure_is_nonfatal` — monkeypatch the insert to raise → prediction still updates, snapshot still published, collector status stays `connected`, one stderr warning.
4. Existing lifecycle tests (start/stop/disconnect) keep passing with the new wiring (`Collector` gains a `db_path`; default unchanged).

## G. Real integration acceptance (manual, release gate)

Not part of pytest — requires a real LM Studio and is run once at release (stage 8):

1. Start the app with the production DB path; open `http://127.0.0.1:8765`.
2. Trigger one real generation in LM Studio (user action; the app only observes).
3. Verify: a new row appears in `~/.lmstudio-speed-viewer/history.db` (e.g. via the history API or a read-only `sqlite3` query); hero UI shows it; `/api/history?range=5m` includes it.
4. Restart **the viewer only** (never LM Studio).
5. Verify: the page immediately shows the last prediction (loaded from SQLite) and history still contains all rows.

## H. Playwright acceptance (`playwright-cli`, release gate)

The eight checks from `docs/v0.2/05-graph-ui-design.md` §9, run against a temp DB via `LM_SPEED_VIEWER_DB`: hero regression, default 1h active + initial fetch, range switching (5m/24h) with observed requests and no reload, graph paths/circles render, exact empty-state text, two distinguishable series + legend, SSE-connect triggers a history refresh, no console errors.

## Coverage (≥ 95%, gate: `pytest --cov=app --cov=db --cov-report=term-missing --cov-fail-under=95`)

The gate widens to include the new `db.py` module (AGENTS.md command updated in stage 8). Hard-to-cover branches and their legitimate tests:

- `db.py` error paths (unwritable parent dir, locked DB) — B.10 and F.3 exercise them with real filesystem/monkeypatch conditions, no exclusions.
- Collector DB-failure branch — F.3 (monkeypatched insert raising).
- API 400 invalid-range branch — D.3.
- The v0.1 `__main__` block (app.py:211-213) remains the only uncovered code; it is already tolerated by the 95% gate (baseline 98.56%) and needs no exclusion.
- No `coverage` exclude directives are added anywhere.

## Flakiness rules

- Every time-dependent assertion uses the injected `now` fixture or offsets from it; no test asserts on real wall-clock values.
- Every DB access uses a per-test temp path; no test reads or writes the production database.
- No test spawns a real `lms` process (existing monkeypatch pattern preserved).

## Verification (this stage)

No product code changed; repository health re-confirmed for this stage: `ruff check .` PASS, `pytest` 22 passed, coverage ≥ 95% gate PASS.
