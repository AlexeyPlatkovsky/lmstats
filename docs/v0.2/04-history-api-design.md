# v0.2 Stage 4 — History Query and Aggregation Design

Inputs: `AGENTS.md`, `docs/v0.2/02-baseline.md`, `docs/v0.2/03-sqlite-design.md`. No product code is implemented in this stage; this document fully specifies the backend history contract.

## 1. API endpoint

```
GET /api/history?range=5m
GET /api/history?range=1h      (default)
GET /api/history?range=24h
```

- `range` is an optional query parameter. Allowed values, exactly: `5m`, `1h`, `24h` (lowercase, case-sensitive).
- Omitted or empty → treated as `1h`.
- Any other value → HTTP **400** with JSON body:

  ```json
  {"error": "invalid range; expected one of: 5m, 1h, 24h"}
  ```

- Success → HTTP **200** with the response structure below. An empty history is a successful 200, not an error.

### Response structure

```json
{
  "range": "1h",
  "generatedAt": "2026-08-15T10:30:00.123Z",
  "series": [
    {
      "model": "qwen3.8-27b-mlx",
      "points": [
        {"timestamp": "2026-08-15T09:31:00.000Z", "avgTokensPerSecond": 15.8, "count": 3}
      ]
    }
  ]
}
```

- `range` — the effective range key (`5m`/`1h`/24h`).
- `generatedAt` — the "now" (ISO-8601 UTC, same format as stored `timestamp`) used to compute the window. Exposing it makes responses deterministic and tells the client where the window ends.
- `series` — one entry per model present in the window (see §6 ordering). A prediction whose `model` is NULL forms a series with `"model": null`.
- `points` — one entry per non-empty bucket for that model, ordered by bucket start ascending (see §3, §6).
- `avgTokensPerSecond` — arithmetic mean of non-NULL `tokens_per_second` in the bucket, rounded to 2 decimals; `null` when every row in the bucket has NULL speed.
- `count` — number of predictions in the bucket, **including** rows with NULL speed.

## 2. Time windows

- `now` = current UTC time at request handling (injected as a parameter in the query function so tests can fix it).
- Window is **closed**: `start = now - duration`, `end = now`; a row qualifies iff `start <= timestamp <= end`.
  - A row exactly at `start` is included; one millisecond earlier is excluded.
  - A row exactly at `end` (the newest possible) is included.

| range | duration |
| --- | --- |
| `5m` | 300 s |
| `1h` | 3600 s |
| `24h` | 86400 s |

All comparisons use the stored ISO-8601 UTC TEXT (fixed-width, lexicographically sortable — stage 3 §3), so plain string comparison in SQL is correct.

## 3. Bucketing (exact deterministic rules)

| range | bucket size | buckets per window |
| --- | --- | --- |
| `5m` | 30 s | 10 |
| `1h` | 60 s (1 minute) | 60 |
| `24h` | 900 s (15 minutes) | 96 |

- Bucket start = `floor(epoch_seconds(timestamp) / size) * size`, i.e. buckets are aligned to **absolute** UTC boundaries (minute buckets always start at `:00.000`, 30 s buckets at `:00`/`:30`, 15 min buckets at `:00`/`:15`).
- Absolute alignment (not relative to `now`) means a row always belongs to the same bucket no matter when the request is made — deterministic across refreshes.
- The point's `timestamp` in the response is the bucket start, formatted as ISO-8601 UTC (stage 3 §3 format).
- Only buckets containing at least one row are emitted; empty buckets produce no point (the client renders gaps).

## 4. Aggregation

- Group rows by `(model, bucket_start)`. Models are never mixed: each model gets its own series.
- Per group: `count` = all rows in the bucket; `avgTokensPerSecond` = mean over rows with `tokens_per_second IS NOT NULL`, rounded to 2 decimals, or `null` if none.
- **Rows with `tokens_per_second = NULL` are excluded from the speed average but included in `count`.**
- Aggregation is computed per request; **no aggregated rows are stored in SQLite** (raw predictions only, per stage 3).

## 5. Empty data

Stable 200 response with an empty series list:

```json
{"range": "1h", "generatedAt": "<now ISO UTC>", "series": []}
```

Same shape for: empty database, window with no rows, and windows where all rows belong to models with NULL speed (those still produce series/points with `avgTokensPerSecond: null`).

## 6. Ordering (deterministic)

- `series`: by `model` ascending, byte-wise; the NULL-model series sorts **last**.
- `points` within a series: by bucket start ascending.

## 7. SQL / query strategy

```sql
SELECT model, timestamp, tokens_per_second
FROM predictions
WHERE timestamp >= :start AND timestamp <= :end
ORDER BY model, timestamp;
```

- The `WHERE` on `timestamp` uses `idx_predictions_timestamp` (stage 3 §4); only rows inside the window are read — never the whole table. For a short range this is a tiny index-bounded scan.
- Only the three needed columns are selected (not `raw_event`/`response`) to keep the scan light.
- Bucketing and aggregation happen in Python over the bounded row set (stage 3 §5 connection pattern: one short-lived connection per request). No SQL datetime arithmetic, no `GROUP BY` in SQL.
- The `idx_predictions_model_timestamp` index remains available for future per-model queries; v0.2 does not require it since the time filter already bounds the scan.

### Module placement

`db.py` (stage 3 §8) gains:

```python
RANGE_DURATIONS = {"5m": 300, "1h": 3600, "24h": 86400}   # seconds
BUCKET_SIZES = {"5m": 30, "1h": 60, "24h": 900}           # seconds

def get_history(path: str, range_key: str, now: datetime) -> dict: ...
```

`get_history` resolves the window from `now`, runs the query, buckets/aggregates per §3–§6, and returns exactly the response body of §1. The FastAPI route `GET /api/history` is a thin wrapper: validate `range` (§1), call `get_history(path, range_key, now=utcnow())`, return the dict as JSON.

## 8. Test matrix

All tests inject a fixed `now` (e.g. `2026-08-15T10:30:00.000Z`) and seed rows at explicit offsets from it; none may depend on the real clock.

1. **5m** — rows at −4 min, −30 s, 0 are returned; a row at −6 min is not.
2. **1h** — rows at −59 min, −1 s, 0 are returned; a row at −2 h is not.
3. **24h** — rows at −23 h, 0 are returned; a row at −25 h is not.
4. **Invalid range** — `range=10m` (and any other value) → 400 with the §1 error body; omitted/empty `range` → 200 behaving as `1h`.
5. **Exact boundaries** — a row exactly at `start` is included; one millisecond before `start` is excluded; a row exactly at `end` is included.
6. **Old rows excluded** — rows older than the window never appear, for any range.
7. **Multiple models separated** — two models with overlapping timestamps produce two series; no point mixes models.
8. **Bucket averages** — a bucket with speeds 10 and 20 → `avgTokensPerSecond` 15.0, `count` 2; rounding to 2 decimals is exact (e.g. 10 + 10.555 → 10.28).
9. **Empty DB** — §5 body, `series: []`, 200.
10. **Missing speed** — a bucket whose rows all have NULL `tokens_per_second` → point with `avgTokensPerSecond: null`, correct `count`; a mixed bucket averages over non-NULL rows only.
11. **Deterministic ordering** — series sorted by model ascending with NULL last; points ascending within a series (assert exact list order).

## Verification (this stage)

No product code changed; repository health re-confirmed for this stage: `ruff check .` PASS, `pytest` 22 passed, coverage ≥ 95% gate PASS.
