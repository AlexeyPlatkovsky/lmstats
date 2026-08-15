"""Shared fixtures for the v0.2 test suite (docs/v0.2/06-test-plan.md)."""

import json
from datetime import datetime, timedelta, timezone

import pytest


@pytest.fixture()
def db_path(tmp_path):
    """Explicit temporary DB path; nothing in the suite may open the production default."""
    return str(tmp_path / "history.db")


@pytest.fixture()
def now():
    """Fixed UTC reference; all time-dependent logic receives this, never the real clock."""
    return datetime(2026, 8, 15, 10, 30, 0, tzinfo=timezone.utc)


@pytest.fixture()
def sample_prediction():
    """Full normalized dict with the values from REAL_EVENT in tests/test_parser.py."""
    return {
        "modelIdentifier": "qwen3.8-27b-mlx",
        "tokensPerSecond": 15.841340338684146,
        "timeToFirstTokenSec": 13.94,
        "totalTimeSec": 6.755,
        "promptTokensCount": 16632,
        "predictedTokensCount": 107,
        "totalTokensCount": 16739,
        "timestampMs": 1786744778242,
        "stopReason": "eosFound",
        "output": "fixture output text",
    }


@pytest.fixture()
def sample_raw_event():
    """The REAL_EVENT JSON as a single line (same content as tests/test_parser.py)."""
    return json.dumps({
        "timestamp": 1786744778242,
        "data": {
            "type": "llm.prediction.output",
            "output": "fixture output text",
            "stats": {
                "stopReason": "eosFound",
                "tokensPerSecond": 15.841340338684146,
                "numGpuLayers": -1,
                "timeToFirstTokenSec": 13.94,
                "totalTimeSec": 6.755,
                "promptTokensCount": 16632,
                "predictedTokensCount": 107,
                "totalTokensCount": 16739,
            },
            "modelIdentifier": "qwen3.8-27b-mlx",
        },
    })


@pytest.fixture()
def seed(db_path, now):
    """Insert one row timestamped `now + ts_offset_s` (stage 3 §3 format)."""
    import db

    epoch = datetime.fromtimestamp(0, tz=timezone.utc)

    def _seed(prediction, *, ts_offset_s=0.0):
        dt = now + timedelta(seconds=ts_offset_s)
        ms = (dt - epoch) // timedelta(milliseconds=1)
        pred = dict(prediction, timestampMs=ms)
        conn = db.connect(db_path)
        try:
            db.insert_prediction(conn, pred, json.dumps({"seeded": True}))
        finally:
            conn.close()

    return _seed
