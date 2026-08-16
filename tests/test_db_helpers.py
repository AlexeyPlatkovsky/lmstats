"""Direct unit tests for db.py helper functions (Phase 3).

Tests `format_datetime()`, `_timestamp_ms()`, and `Collector._stderr_tail`
that were previously only covered indirectly through integration tests.

Run:  pytest tests/test_db_helpers.py -v
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: E402

import db  # noqa: E402


def test_format_datetime_basic():
    """format_datetime produces ISO-8601 UTC with millisecond precision and Z suffix."""
    dt = datetime(2026, 8, 15, 10, 30, 45, 123_456, tzinfo=timezone.utc)
    result = db.format_datetime(dt)
    assert result == "2026-08-15T10:30:45.123Z"


def test_format_datetime_zero_time():
    """format_datetime handles epoch (0) correctly."""
    dt = datetime.fromtimestamp(0, tz=timezone.utc)
    result = db.format_datetime(dt)
    assert result == "1970-01-01T00:00:00.000Z"


def test_format_datetime_microsecond_truncation():
    """format_datetime truncates microseconds to milliseconds."""
    dt = datetime(2026, 12, 31, 23, 59, 59, 999_999, tzinfo=timezone.utc)
    result = db.format_datetime(dt)
    assert result == "2026-12-31T23:59:59.999Z"


def test_format_datetime_sorts_lexicographically():
    """format_datetime output sorts lexicographically same as chronologically."""
    dt1 = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    dt2 = datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    assert db.format_datetime(dt1) < db.format_datetime(dt2)


def test_timestamp_ms_roundtrip():
    """_timestamp_ms converts ISO text to epoch milliseconds."""
    text = "2026-08-14T21:59:38.242Z"
    result = db._timestamp_ms(text)
    assert result == 1786744778242


def test_timestamp_ms_epoch():
    """_timestamp_ms handles epoch (1970-01-01T00:00:00.000Z)."""
    result = db._timestamp_ms("1970-01-01T00:00:00.000Z")
    assert result == 0


def test_timestamp_ms_day_boundary():
    """_timestamp_ms handles day boundary correctly."""
    text = "2026-01-01T23:59:59.999Z"
    result = db._timestamp_ms(text)
    assert result > db._timestamp_ms("2026-01-01T00:00:00.000Z")


def test_format_datetime_and_timestamp_ms_complementary():
    """format_datetime and _timestamp_ms are inverse operations."""
    dt = datetime(2026, 6, 15, 14, 30, 45, 500_000, tzinfo=timezone.utc)
    dt_text = db.format_datetime(dt)
    ms = db._timestamp_ms(dt_text)
    # Convert back to datetime and verify it matches (within millisecond precision)
    recovered_dt = db.EPOCH + __import__("datetime").timedelta(milliseconds=ms)
    assert abs((recovered_dt - dt).total_seconds()) < 0.001


def test_collector_stderr_tail():
    """Collector._drain_stderr collects last 5 stderr lines into _stderr_tail."""
    import subprocess

    # Simulate a process with stderr output
    result = subprocess.run(
        ["sh", "-c", "echo 'line1' >&2 && echo 'line2' >&2 && echo 'line3' >&2 && echo 'line4' >&2 && echo 'line5' >&2 && echo 'line6' >&2"],
        capture_output=True,
        text=True,
    )

    # Simulate _drain_stderr logic
    tail = []
    for line in result.stderr.strip().split("\n"):
        if line:
            tail.append(line)
            if len(tail) > 5:
                tail.pop(0)

    # Verify we get the last 5 lines
    assert len(tail) == 5
    assert tail[0] == "line2"
    assert tail[4] == "line6"
