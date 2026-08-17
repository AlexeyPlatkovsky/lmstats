"""Tests for the SQLite persistence layer (stage 6 group B)."""

import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: E402

import db  # noqa: E402


def test_init_creates_schema(tmp_path):
    path = str(tmp_path / "nested" / "dir" / "history.db")  # parent dir must be auto-created
    db.init_db(path)
    conn = db.connect(path)
    try:
        names = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'index')")}
    finally:
        conn.close()
    assert "predictions" in names
    assert "idx_predictions_timestamp" in names
    assert "idx_predictions_model_timestamp" in names


def test_init_idempotent(db_path, sample_prediction):
    db.init_db(db_path)
    conn = db.connect(db_path)
    try:
        db.insert_prediction(conn, sample_prediction, "raw")
    finally:
        conn.close()
    db.init_db(db_path)  # again, after inserts: no error, data unchanged
    conn = db.connect(db_path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0] == 1
    finally:
        conn.close()


def test_insert_roundtrip(db_path, sample_prediction, sample_raw_event):
    db.init_db(db_path)
    conn = db.connect(db_path)
    try:
        rowid = db.insert_prediction(conn, sample_prediction, sample_raw_event)
    finally:
        conn.close()
    assert rowid == 1
    conn = db.connect(db_path)
    try:
        row = conn.execute("SELECT * FROM predictions WHERE id = ?", (rowid,)).fetchone()
    finally:
        conn.close()
    assert row["timestamp"] == "2026-08-14T21:59:38.242Z"
    assert row["model"] == "qwen3.8-27b-mlx"
    assert row["tokens_per_second"] == 15.841340338684146
    assert row["time_to_first_token_seconds"] == 13.94
    assert row["total_time_seconds"] == 6.755
    assert row["prompt_tokens"] == 16632
    assert row["output_tokens"] == 107
    assert row["total_tokens"] == 16739
    assert row["stop_reason"] == "eosFound"
    assert row["response"] == "fixture output text"
    assert row["raw_event"] == sample_raw_event


def test_latest_returns_newest(db_path, seed, sample_prediction):
    db.init_db(db_path)
    seed(dict(sample_prediction, modelIdentifier="t-10s"), ts_offset_s=-10)
    seed(dict(sample_prediction, modelIdentifier="t-5s"), ts_offset_s=-5)
    seed(dict(sample_prediction, modelIdentifier="t0"))
    conn = db.connect(db_path)
    try:
        assert db.latest_prediction(conn)["modelIdentifier"] == "t0"
    finally:
        conn.close()


def test_latest_tie_broken_by_later_id(tmp_path, sample_prediction):
    path = str(tmp_path / "tie.db")
    db.init_db(path)
    conn = db.connect(path)
    try:
        for model in ("first", "second"):  # equal timestamps (same timestampMs)
            db.insert_prediction(conn, dict(sample_prediction, modelIdentifier=model), "raw")
    finally:
        conn.close()
    conn = db.connect(path)
    try:
        assert db.latest_prediction(conn)["modelIdentifier"] == "second"
    finally:
        conn.close()


def test_latest_empty_db(db_path):
    db.init_db(db_path)
    conn = db.connect(db_path)
    try:
        assert db.latest_prediction(conn) is None
    finally:
        conn.close()


def test_persistence_across_reopen(db_path, sample_prediction):
    db.init_db(db_path)
    conn = db.connect(db_path)
    try:
        db.insert_prediction(conn, sample_prediction, "raw")
    finally:
        conn.close()  # all connections closed; reopen fresh below
    conn = db.connect(db_path)
    try:
        latest = db.latest_prediction(conn)
    finally:
        conn.close()
    assert latest is not None
    assert latest["modelIdentifier"] == "qwen3.8-27b-mlx"
    assert latest["tokensPerSecond"] == 15.841340338684146
    assert latest["timestampMs"] == 1786744778242


def test_null_optional_fields(db_path):
    db.init_db(db_path)
    pred = {
        "modelIdentifier": None,
        "tokensPerSecond": None,
        "timeToFirstTokenSec": None,
        "totalTimeSec": None,
        "promptTokensCount": None,
        "predictedTokensCount": None,
        "totalTokensCount": None,
        "timestampMs": 1786744778242,
        "stopReason": None,
        "output": None,
    }
    conn = db.connect(db_path)
    try:
        rowid = db.insert_prediction(conn, pred, "raw")
        latest = db.latest_prediction(conn)  # still returned by latest
    finally:
        conn.close()
    assert rowid == 1
    assert latest is not None
    for key in ("modelIdentifier", "tokensPerSecond", "timeToFirstTokenSec",
                "totalTimeSec", "promptTokensCount", "predictedTokensCount",
                "totalTokensCount", "stopReason", "output"):
        assert latest[key] is None
    assert latest["timestampMs"] == 1786744778242


def test_timestamp_format():
    # exact millisecond precision, no float drift
    assert db.format_timestamp(1786744778242) == "2026-08-14T21:59:38.242Z"
    assert db.format_timestamp(0) == "1970-01-01T00:00:00.000Z"
    # fixed-width Z format; lexicographic order matches chronological order
    assert db.format_timestamp(1_000) < db.format_timestamp(2_000)
    assert db.format_timestamp(86_399_123) < db.format_timestamp(86_400_000)  # day boundary
    # None input -> valid "now" format; assert shape/monotonicity only, never wall-clock
    now_text = db.format_timestamp(None)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z", now_text)
    assert now_text > db.format_timestamp(0)


def test_default_path_override(monkeypatch):
    monkeypatch.setenv("LMSTATS_DB", "/tmp/custom-history.db")
    assert db.default_db_path() == "/tmp/custom-history.db"
    monkeypatch.delenv("LMSTATS_DB")
    monkeypatch.setattr(os.path, "expanduser", lambda p: "/fake/home" + p[1:])
    expected = os.path.join("/fake/home", ".lmstats", "history.db")
    assert db.default_db_path() == expected


def test_insert_failure_isolated(tmp_path, sample_prediction):
    # Unwritable parent dir: the failure propagates out of the db layer (the
    # collector, not this module, decides it is non-fatal — group F).
    parent = tmp_path / "ro"
    parent.mkdir()
    os.chmod(parent, 0o555)
    try:
        path = str(parent / "history.db")

        def attempt():
            conn = db.connect(path)
            try:
                return db.insert_prediction(conn, sample_prediction, "raw")
            finally:
                conn.close()

        with pytest.raises(sqlite3.OperationalError):
            attempt()
    finally:
        os.chmod(parent, 0o755)  # restore so tmp cleanup works
