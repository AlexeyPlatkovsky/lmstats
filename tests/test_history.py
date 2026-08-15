"""Tests for the history query and aggregation (stage 6 group C).

All tests seed rows against the fixed `now` fixture and call
db.get_history(path, range_key, now=now); none may read the real clock.
"""

import os
import sys
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import db  # noqa: E402


def _init(db_path):
    db.init_db(db_path)


def test_range_5m(db_path, seed, now):
    _init(db_path)
    p = {"modelIdentifier": "m", "tokensPerSecond": 10.0}
    seed(p, ts_offset_s=-4 * 60)   # in window
    seed(p, ts_offset_s=-30)        # in window
    seed(p)                         # exactly now: in window (closed end)
    seed(p, ts_offset_s=-6 * 60)    # before window start: excluded
    body = db.get_history(db_path, "5m", now=now)
    assert body["range"] == "5m"
    assert len(body["series"]) == 1
    points = body["series"][0]["points"]
    assert [pt["timestamp"] for pt in points] == [
        "2026-08-15T10:26:00.000Z",  # -4 min, its own 30 s bucket
        "2026-08-15T10:29:30.000Z",  # -30 s
        "2026-08-15T10:30:00.000Z",  # now
    ]
    assert all(pt["count"] == 1 for pt in points)


def test_range_1h(db_path, seed, now):
    _init(db_path)
    p = {"modelIdentifier": "m", "tokensPerSecond": 10.0}
    seed(p, ts_offset_s=-59 * 60)   # in window
    seed(p, ts_offset_s=-1)          # in window
    seed(p)                          # exactly now: in window
    seed(p, ts_offset_s=-2 * 3600)   # before window start: excluded
    body = db.get_history(db_path, "1h", now=now)
    points = body["series"][0]["points"]
    assert [pt["timestamp"] for pt in points] == [
        "2026-08-15T09:31:00.000Z",  # -59 min, minute bucket
        "2026-08-15T10:29:00.000Z",  # -1 s, minute bucket
        "2026-08-15T10:30:00.000Z",  # now
    ]


def test_range_24h(db_path, seed, now):
    _init(db_path)
    p = {"modelIdentifier": "m", "tokensPerSecond": 10.0}
    seed(p, ts_offset_s=-23 * 3600)   # in window
    seed(p)                            # exactly now: in window
    seed(p, ts_offset_s=-25 * 3600)    # before window start: excluded
    body = db.get_history(db_path, "24h", now=now)
    points = body["series"][0]["points"]
    assert [pt["timestamp"] for pt in points] == [
        "2026-08-14T11:30:00.000Z",  # -23 h, 15 min bucket
        "2026-08-15T10:30:00.000Z",  # now
    ]


def test_boundary_inclusive(db_path, seed, now):
    _init(db_path)
    p = {"modelIdentifier": "m", "tokensPerSecond": 10.0}
    seed(p, ts_offset_s=-300)      # exactly window start (5m): included
    seed(p, ts_offset_s=-300.001)  # one ms before start: excluded
    seed(p)                        # exactly now (window end): included
    body = db.get_history(db_path, "5m", now=now)
    points = body["series"][0]["points"]
    assert [pt["timestamp"] for pt in points] == [
        "2026-08-15T10:25:00.000Z",
        "2026-08-15T10:30:00.000Z",
    ]


def test_multiple_models_separated(db_path, seed, now):
    _init(db_path)
    a = {"modelIdentifier": "alpha", "tokensPerSecond": 10.0}
    b = {"modelIdentifier": "beta", "tokensPerSecond": 20.0}
    seed(a, ts_offset_s=-10)  # overlapping times on purpose
    seed(b, ts_offset_s=-10)
    body = db.get_history(db_path, "5m", now=now)
    assert [s["model"] for s in body["series"]] == ["alpha", "beta"]
    for series in body["series"]:
        assert len(series["points"]) == 1
        assert series["points"][0]["count"] == 1  # no point mixes models


def test_bucket_average(db_path, seed, now):
    _init(db_path)
    p10 = {"modelIdentifier": "m", "tokensPerSecond": 10.0}
    p20 = {"modelIdentifier": "m", "tokensPerSecond": 20.0}
    seed(p10, ts_offset_s=-5)   # same minute bucket as -10 s
    seed(p20, ts_offset_s=-10)
    # rounding case in a different bucket: 10 + 10.555 -> 10.28
    seed(p10, ts_offset_s=-65)
    seed({"modelIdentifier": "m", "tokensPerSecond": 10.555}, ts_offset_s=-70)
    body = db.get_history(db_path, "1h", now=now)
    points = {pt["timestamp"]: pt for pt in body["series"][0]["points"]}
    assert points["2026-08-15T10:29:00.000Z"] == {
        "timestamp": "2026-08-15T10:29:00.000Z",
        "avgTokensPerSecond": 15.0,
        "count": 2,
    }
    assert points["2026-08-15T10:28:00.000Z"]["avgTokensPerSecond"] == 10.28
    assert points["2026-08-15T10:28:00.000Z"]["count"] == 2


def test_bucket_alignment(db_path, seed, now):
    _init(db_path)
    p = {"modelIdentifier": "m", "tokensPerSecond": 10.0}
    seed(p, ts_offset_s=45)  # 10:30:45; request "now" is later so the row is in window
    body = db.get_history(db_path, "1h", now=now + timedelta(seconds=60))
    assert [pt["timestamp"] for pt in body["series"][0]["points"]] == [
        "2026-08-15T10:30:00.000Z"  # absolute minute alignment, not relative to now
    ]


def test_null_speed_excluded_from_average(db_path, seed, now):
    _init(db_path)
    with_speed = {"modelIdentifier": "m", "tokensPerSecond": 20.0}
    without = {"modelIdentifier": "m", "tokensPerSecond": None}
    seed(with_speed, ts_offset_s=-5)   # mixed bucket: avg over non-NULL only
    seed(without, ts_offset_s=-10)
    seed({"modelIdentifier": "n", "tokensPerSecond": None}, ts_offset_s=-5)  # all-NULL bucket
    body = db.get_history(db_path, "1h", now=now)
    by_model = {s["model"]: s for s in body["series"]}
    mixed = by_model["m"]["points"][0]
    assert mixed == {
        "timestamp": "2026-08-15T10:29:00.000Z",
        "avgTokensPerSecond": 20.0,
        "count": 2,  # NULL-speed row still counted
    }
    assert by_model["n"]["points"][0]["avgTokensPerSecond"] is None
    assert by_model["n"]["points"][0]["count"] == 1


def test_empty_db(db_path, now):
    _init(db_path)
    body = db.get_history(db_path, "1h", now=now)
    assert body == {
        "range": "1h",
        "generatedAt": "2026-08-15T10:30:00.000Z",
        "series": [],
    }


def test_deterministic_ordering(db_path, seed, now):
    _init(db_path)
    zeta = {"modelIdentifier": "zeta", "tokensPerSecond": 1.0}
    alpha = {"modelIdentifier": "alpha", "tokensPerSecond": 2.0}
    unknown = {"modelIdentifier": None, "tokensPerSecond": 3.0}
    seed(zeta)
    seed(alpha, ts_offset_s=-120)  # two points for alpha, out of order on purpose
    seed(alpha, ts_offset_s=-60)
    seed(unknown)
    body = db.get_history(db_path, "1h", now=now)
    assert [s["model"] for s in body["series"]] == ["alpha", "zeta", None]  # NULL last
    alpha_points = body["series"][0]["points"]
    assert [pt["timestamp"] for pt in alpha_points] == [
        "2026-08-15T10:28:00.000Z",
        "2026-08-15T10:29:00.000Z",
    ]
