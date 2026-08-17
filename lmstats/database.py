"""SQLite persistence for LM Stats Viewer v0.2 (docs/v0.2/03-sqlite-design.md).

One database file, one `predictions` table, two indexes. Every valid completed
prediction is inserted exactly once; the latest row loads on startup; history
survives viewer restart. One short-lived connection per operation; no ORM, no
migrations, no new dependencies.
"""

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from statistics import median

SCHEMA = """
CREATE TABLE IF NOT EXISTS predictions (
  id                          INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp                   TEXT    NOT NULL,
  model                       TEXT,
  tokens_per_second           REAL,
  time_to_first_token_seconds REAL,
  total_time_seconds          REAL,
  prompt_tokens               INTEGER,
  output_tokens               INTEGER,
  total_tokens                INTEGER,
  stop_reason                 TEXT,
  response                    TEXT,
  raw_event                   TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_predictions_timestamp
  ON predictions (timestamp, id);

CREATE INDEX IF NOT EXISTS idx_predictions_model_timestamp
  ON predictions (model, timestamp);
"""

EPOCH = datetime.fromtimestamp(0, tz=timezone.utc)


def default_db_path() -> str:
    """Env LMSTATS_DB override, else ~/.lmstats/history.db."""
    env = os.environ.get("LMSTATS_DB")
    if env:
        return env
    return os.path.join(os.path.expanduser("~"), ".lmstats", "history.db")


def init_db(path: str) -> None:
    """Create the parent dir, set WAL, and apply the idempotent schema."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with closing(connect(path)) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(SCHEMA)
        conn.commit()


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def format_datetime(dt: datetime) -> str:
    """ISO-8601 UTC with millisecond precision and a Z suffix (fixed width, sortable)."""
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def format_timestamp(ms: int | None) -> str:
    """Epoch milliseconds in the storage format; None means "now" at call time."""
    if ms is None:
        return format_datetime(datetime.now(timezone.utc))
    return format_datetime(EPOCH + timedelta(milliseconds=int(ms)))


def _timestamp_ms(text: str) -> int:
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    return (dt - EPOCH) // timedelta(milliseconds=1)


def insert_prediction(conn: sqlite3.Connection, pred: dict, raw_line: str) -> int:
    """Insert one normalized prediction; returns the new rowid."""
    cur = conn.execute(
        """INSERT INTO predictions (
               timestamp, model, tokens_per_second, time_to_first_token_seconds,
               total_time_seconds, prompt_tokens, output_tokens, total_tokens,
               stop_reason, response, raw_event)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            format_timestamp(pred.get("timestampMs")),
            pred.get("modelIdentifier"),
            pred.get("tokensPerSecond"),
            pred.get("timeToFirstTokenSec"),
            pred.get("totalTimeSec"),
            pred.get("promptTokensCount"),
            pred.get("predictedTokensCount"),
            pred.get("totalTokensCount"),
            pred.get("stopReason"),
            pred.get("output"),
            raw_line,
        ),
    )
    conn.commit()
    return cur.lastrowid


def row_to_prediction(row: sqlite3.Row) -> dict:
    """Row back to the normalized camelCase shape (identical keys to parse_line)."""
    return {
        "modelIdentifier": row["model"],
        "tokensPerSecond": row["tokens_per_second"],
        "timeToFirstTokenSec": row["time_to_first_token_seconds"],
        "totalTimeSec": row["total_time_seconds"],
        "promptTokensCount": row["prompt_tokens"],
        "predictedTokensCount": row["output_tokens"],
        "totalTokensCount": row["total_tokens"],
        "timestampMs": _timestamp_ms(row["timestamp"]),
        "stopReason": row["stop_reason"],
        "output": row["response"],
    }


def latest_prediction(conn: sqlite3.Connection) -> dict | None:
    """The row with max (timestamp, id), or None on an empty database."""
    row = conn.execute(
        "SELECT * FROM predictions ORDER BY timestamp DESC, id DESC LIMIT 1"
    ).fetchone()
    return row_to_prediction(row) if row is not None else None


RANGE_DURATIONS = {"5m": 300, "15m": 900, "1h": 3600, "24h": 86400, "1mo": 2592000}
BUCKET_SIZES = {"5m": 30, "15m": 60, "1h": 60, "24h": 900, "1mo": 86400}
MAX_DASHBOARD_WINDOW = timedelta(days=7)


def get_history(path: str, range_key: str, now: datetime) -> dict:
    """Bucketed per-model speed history for the window ending at `now`.

    Reads only rows inside [now - duration, now] (stage 4 §2), buckets them by
    absolute UTC boundaries (stage 4 §3), and aggregates per (model, bucket) in
    Python. Nothing aggregated is stored; models are never mixed.
    """
    now_ms = _timestamp_ms(format_datetime(now))
    start_text = format_timestamp(now_ms - RANGE_DURATIONS[range_key] * 1000)
    end_text = format_timestamp(now_ms)
    bucket_ms = BUCKET_SIZES[range_key] * 1000

    with closing(connect(path)) as conn:
        rows = conn.execute(
            "SELECT model, timestamp, tokens_per_second FROM predictions"
            " WHERE timestamp >= ? AND timestamp <= ? ORDER BY model, timestamp",
            (start_text, end_text),
        ).fetchall()

    buckets: dict[tuple, list] = {}
    for row in rows:
        key = (row["model"], _timestamp_ms(row["timestamp"]) // bucket_ms * bucket_ms)
        agg = buckets.setdefault(key, [0, 0.0, 0])  # count, speed sum, non-null n
        agg[0] += 1
        if row["tokens_per_second"] is not None:
            agg[1] += row["tokens_per_second"]
            agg[2] += 1

    series: dict = {}
    for (model, bucket_start), (count, speed_sum, speed_n) in buckets.items():
        avg = round(speed_sum / speed_n, 2) if speed_n else None
        series.setdefault(model, []).append({
            "timestamp": format_timestamp(bucket_start),
            "avgTokensPerSecond": avg,
            "count": count,
        })

    ordered = [
        {"model": model, "points": sorted(points, key=lambda p: p["timestamp"])}
        for model, points in sorted(
            series.items(), key=lambda item: (item[0] is None, item[0] or ""))
    ]
    return {
        "range": range_key,
        "generatedAt": format_datetime(now),
        "series": ordered,
    }


def get_dashboard(
    path: str, start: datetime, end: datetime, range_key: str,
) -> dict:
    """Return the raw-window dashboard data without storing derived values."""
    start_text = format_datetime(start)
    end_text = format_datetime(end)
    custom_bucket = max(10, int((end - start).total_seconds() / 120))
    bucket_ms = BUCKET_SIZES.get(range_key, custom_bucket) * 1000

    with closing(connect(path)) as conn:
        rows = conn.execute(
            "SELECT * FROM predictions WHERE timestamp >= ? AND timestamp <= ?"
            " ORDER BY timestamp DESC, id DESC",
            (start_text, end_text),
        ).fetchall()
        recent_rows = conn.execute(
            "SELECT * FROM predictions ORDER BY timestamp DESC, id DESC LIMIT 8"
        ).fetchall()

    recent = [row_to_prediction(row) for row in recent_rows]
    by_model: dict = {}
    buckets: dict[tuple, list] = {}
    for row in rows:
        model = row["model"]
        values = by_model.setdefault(model, {
            "requests": 0, "speeds": [], "ttfts": [], "prompt": 0, "output": 0,
        })
        values["requests"] += 1
        if row["tokens_per_second"] is not None:
            values["speeds"].append(row["tokens_per_second"])
        if row["time_to_first_token_seconds"] is not None:
            values["ttfts"].append(row["time_to_first_token_seconds"])
        values["prompt"] += row["prompt_tokens"] or 0
        values["output"] += row["output_tokens"] or 0

        bucket_start = _timestamp_ms(row["timestamp"]) // bucket_ms * bucket_ms
        bucket = buckets.setdefault((model, bucket_start), [0, 0.0, 0])
        bucket[0] += 1
        if row["tokens_per_second"] is not None:
            bucket[1] += row["tokens_per_second"]
            bucket[2] += 1

    ordered_models = sorted(by_model, key=lambda model: (model is None, model or ""))
    summary = []
    for model in ordered_models:
        values = by_model[model]
        speeds = values["speeds"]
        ttfts = values["ttfts"]
        summary.append({
            "model": model,
            "requests": values["requests"],
            "avgTokensPerSecond": round(sum(speeds) / len(speeds), 2) if speeds else None,
            "medianTokensPerSecond": round(median(speeds), 2) if speeds else None,
            "minTokensPerSecond": round(min(speeds), 2) if speeds else None,
            "maxTokensPerSecond": round(max(speeds), 2) if speeds else None,
            "avgTimeToFirstTokenSec": round(sum(ttfts) / len(ttfts), 2) if ttfts else None,
            "promptTokens": values["prompt"],
            "outputTokens": values["output"],
        })

    if range_key == "1mo":
        raw_points: dict = {}
        for row in reversed(rows):
            if row["tokens_per_second"] is not None:
                raw_points.setdefault(row["model"], []).append({
                    "timestamp": row["timestamp"],
                    "avgTokensPerSecond": row["tokens_per_second"],
                    "count": 1,
                })
        history_series = [
            {"model": model, "points": points[-10:]}
            for model, points in sorted(
                raw_points.items(), key=lambda item: (item[0] is None, item[0] or "")
            )
        ]
    else:
        series: dict = {}
        for (model, bucket_start), (count, speed_sum, speed_n) in buckets.items():
            series.setdefault(model, []).append({
                "timestamp": format_timestamp(bucket_start),
                "avgTokensPerSecond": round(speed_sum / speed_n, 2) if speed_n else None,
                "count": count,
            })
        history_series = [
            {"model": model, "points": sorted(series[model], key=lambda point: point["timestamp"])}
            for model in sorted(series, key=lambda model: (model is None, model or ""))
        ]
    history = {
        "range": range_key,
        "generatedAt": end_text,
        "series": history_series,
    }
    return {
        "range": range_key,
        "start": start_text,
        "end": end_text,
        "history": history,
        "recent": recent,
        "summary": summary,
    }
