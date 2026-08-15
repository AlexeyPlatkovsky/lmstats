# v0.2 Stage 3 — SQLite Persistence Design

Inputs: `AGENTS.md`, `docs/v0.2/02-baseline.md`. No product code is implemented in this stage; this document fully specifies the persistence layer so a fresh agent can implement it without prior context.

## Design summary

- Python built-in `sqlite3` only. No ORM, no migration framework, no new dependencies.
- One database file, one `predictions` table, two indexes.
- Every valid completed prediction is inserted exactly once; the latest row is loadable on startup; history survives viewer restart.
- Persistence never depends on an attached browser and never blocks or breaks the live view.

## 1. Database location

Default path:

```
~/.lmstudio-speed-viewer/history.db
```

Rationale: predictable and user-visible; outside the repository (no `.gitignore` changes, no risk of committing data); history follows the user across repo moves/renames; survives viewer restart.

Override: environment variable `LM_SPEED_VIEWER_DB` (full file path) takes precedence over the default. The storage API always accepts an explicit `path` argument; the env/default resolution lives in one helper so tests can pass a temporary path directly without mutating any global.

Test isolation: every test passes an explicit temporary path (pytest `tmp_path`). Nothing in the test suite may open the default production path.

## 2. Schema

Single table, created with `CREATE TABLE IF NOT EXISTS`:

```sql
CREATE TABLE IF NOT EXISTS predictions (
  id                          INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp                   TEXT    NOT NULL,  -- ISO-8601 UTC, see §3
  model                       TEXT,              -- nullable
  tokens_per_second           REAL,              -- nullable
  time_to_first_token_seconds REAL,              -- nullable
  total_time_seconds          REAL,              -- nullable
  prompt_tokens               INTEGER,           -- nullable
  output_tokens               INTEGER,           -- nullable
  total_tokens                INTEGER,           -- nullable
  stop_reason                 TEXT,              -- nullable (new in v0.2)
  response                    TEXT,              -- nullable; generated output text (new in v0.2)
  raw_event                   TEXT    NOT NULL   -- original lms JSON line, verbatim (stripped)
);
```

Nullability rules:

- `timestamp` is NOT NULL. If the event carries no usable `timestampMs`, the insert uses the current UTC time at insertion (the moment the viewer observed completion). Every row stays orderable and range-queryable.
- All stat fields are nullable: the parser already maps missing/wrong-typed values to `None`, and a prediction with partial stats is still stored.
- `raw_event` is NOT NULL: every row originates from a parsed line, so the raw text always exists. It preserves fields lms may add later and aids debugging.

Deliberately excluded (per stage brief): cache fields, internal-request classification, analytics/aggregation tables, retention policy, user settings.

### Parser change required to fill the new columns

The v0.1 parser drops `stats.stopReason` and `data.output`. The normalized dict gains two keys (existing keys unchanged):

| Normalized key | Source | Type |
| --- | --- | --- |
| `stopReason` | `data.stats.stopReason` | str or None (non-str → None) |
| `output` | `data.output` | str or None (non-str → None) |

Column mapping: normalized `output` → column `response`; all other keys map by the obvious name (`modelIdentifier`→`model`, `tokensPerSecond`→`tokens_per_second`, `timeToFirstTokenSec`→`time_to_first_token_seconds`, `totalTimeSec`→`total_time_seconds`, `promptTokensCount`→`prompt_tokens`, `predictedTokensCount`→`output_tokens`, `totalTokensCount`→`total_tokens`).

## 3. Timestamp policy

One unambiguous storage format: **ISO-8601 UTC with millisecond precision and a `Z` suffix**, e.g. `2026-08-15T10:30:00.123Z`.

- Fixed width and lexicographically sortable, so `WHERE timestamp >= ? AND timestamp < ?` works on TEXT with plain string comparison — no SQLite datetime functions needed.
- Derivation from the event: `timestampMs` is epoch milliseconds (integer). Convert without float drift:

  ```python
  dt = datetime.fromtimestamp(0, tz=timezone.utc) + timedelta(milliseconds=int(ms))
  text = dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")
  ```

- Fallback when `timestampMs` is missing/invalid: the same formatting applied to "now" at insertion time.
- Local browser time is derived client-side: the API returns timestamps in this exact format, and the frontend renders them with `new Date(value)` + `toLocale*` calls. The server never emits local-time strings.

## 4. Indexes

Only the two indexes needed by the v0.2 query set (latest, time range, per-model time range):

```sql
CREATE INDEX IF NOT EXISTS idx_predictions_timestamp
  ON predictions (timestamp, id);

CREATE INDEX IF NOT EXISTS idx_predictions_model_timestamp
  ON predictions (model, timestamp);
```

- `idx_predictions_timestamp` serves latest (`ORDER BY timestamp DESC, id DESC LIMIT 1`) and plain time-range scans; the `id` tie-break makes "latest" deterministic when two rows share a timestamp (later insert wins).
- `idx_predictions_model_timestamp` serves per-model time-range queries.
- No other indexes in v0.2.

## 5. Connection strategy

**One short-lived connection per operation.** No shared, long-lived connection anywhere.

```python
def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn
```

Each operation opens its own connection, does its work, and closes it (use `contextlib.closing`). Rationale:

- FastAPI sync endpoints run in a thread pool; `sqlite3` connections are not shareable across threads (`check_same_thread`). Per-operation connections make that hazard impossible by construction.
- Write frequency is one row per completed generation; read frequency is user-initiated. Connection setup cost is negligible for a local tool.
- `PRAGMA journal_mode=WAL` is set during schema init; it persists in the database file, so a reader and the writer can coexist without lock errors. Re-asserting it on connect is harmless but not required.

## 6. Persistence flow

```
lms stdout line
  → parse_line()                      (existing; gains stopReason/output)
  → normalized dict or None           (None: line ignored, as in v0.1)
  → db.insert_prediction(conn, pred, raw_line)   ← new; one INSERT per valid prediction
  → collector.prediction = pred       (existing latest-state update)
  → collector.publish()               (existing SSE notification)
```

Rules:

- The insert happens in `Collector._run()` at the existing choke point (baseline doc §extension points), so persistence works with zero attached browsers.
- A database failure is **non-fatal**: catch the exception, print a one-line warning to stderr, then continue with latest-state update + publish. The live view and collector status are never degraded by a DB problem; no new UI state is introduced.
- The raw line passed to the insert is the original stripped line text from stdout (the same string `parse_line` received).

## 7. Startup behavior

In the FastAPI lifespan, before `collector.start()`:

1. Resolve the DB path (env override or default) and ensure the parent directory exists (`os.makedirs(..., exist_ok=True)`).
2. `init_db(path)`: open a connection, set WAL, run the `CREATE TABLE IF NOT EXISTS` + both `CREATE INDEX IF NOT EXISTS` statements, close. Idempotent — safe on every start; an existing database file is preserved as-is (never deleted or recreated).
3. `latest = latest_prediction(path)`: `SELECT ... ORDER BY timestamp DESC, id DESC LIMIT 1`; map the row back to the normalized dict shape (camelCase keys identical to `parse_line` output) or None.
4. If a row exists, set `collector.prediction = latest` **before** starting the live stream, so the UI immediately shows the last known prediction instead of "Waiting for first prediction" after a restart.
5. `await collector.start()` — live collection proceeds exactly as in v0.1; new events append rows and replace the latest state.

## 8. Module layout

New file `db.py` at the repository root (next to `app.py`); `app.py` imports it. Keeping parser/collector/HTTP in `app.py` and storage in `db.py` preserves the baseline's "concerns separate" rule while keeping the change small.

```python
SCHEMA = """..."""                       # §2 DDL + §4 indexes

def default_db_path() -> str: ...        # env LM_SPEED_VIEWER_DB or ~/.lmstudio-speed-viewer/history.db
def init_db(path: str) -> None: ...      # makedirs + WAL + idempotent schema
def connect(path: str) -> sqlite3.Connection: ...   # row_factory = sqlite3.Row
def format_timestamp(ms: int | None) -> str: ...    # §3; None → now
def insert_prediction(conn, pred: dict, raw_line: str) -> int: ...   # returns rowid
def latest_prediction(conn) -> dict | None: ...    # normalized shape, or None
def row_to_prediction(row) -> dict: ...  # row → camelCase normalized dict (shared by latest + history queries)
```

The time-range query function is specified in `docs/v0.2/04-history-api-design.md` and lives in the same module.

## 9. Test cases (to be added with the implementation)

All tests use an explicit temporary DB path (`tmp_path`); none may touch the production default.

1. **New DB** — `init_db` on a fresh path creates the table and both indexes; `latest_prediction` returns None on an empty DB.
2. **Schema idempotence** — `init_db` twice (and after inserts) raises nothing and changes no data.
3. **Insert** — a full prediction round-trips: every column value equals the input; rowid is returned.
4. **Latest lookup** — with several rows, returns the one with max `(timestamp, id)`; a later-inserted row with an equal timestamp wins.
5. **Persistence across reopen** — insert, close all connections, `connect` again: rows and latest survive.
6. **Null optional fields** — a prediction with `model`/stats all None stores NULLs and reads back as None; the row is still returned by latest.
7. **Timestamp normalization** — `format_timestamp` is exact at millisecond precision (no float drift), produces the `Z`-suffixed fixed-width format, and is lexicographically ordered; missing input falls back to "now" (assert only format/monotonicity, never an exact wall-clock value). Window boundary inclusion/exclusion is asserted at the history layer (`04-history-api-design.md` §8, `06-test-plan.md` C.4), which relies on this format's lexicographic ordering.
8. **Test DB isolation** — the suite never opens `default_db_path()`; a test asserts inserts land only in the temp path.

## Verification (this stage)

No product code changed; repository health re-confirmed for this stage: `ruff check .` PASS, `pytest` 22 passed, coverage 98.56% (≥ 95% gate PASS).
