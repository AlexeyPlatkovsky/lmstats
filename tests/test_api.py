"""Tests for the HTTP routes and the SSE endpoint."""

import asyncio
import json
import os
import sys
from datetime import timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from lm_speed_viewer import collector as collector_module  # noqa: E402
from lm_speed_viewer import database  # noqa: E402
from lm_speed_viewer.application import create_app, utcnow  # noqa: E402
from lm_speed_viewer.collector import Collector  # noqa: E402
from lm_speed_viewer.parser import PREDICTION_TYPE  # noqa: E402
from starlette.requests import Request  # noqa: E402


def test_utcnow_is_timezone_aware_utc():
    """History windows must use an aware UTC clock when not overridden by tests."""
    assert utcnow().tzinfo is timezone.utc


@pytest.fixture()
def client(monkeypatch, tmp_path, now):
    """TestClient with the lms CLI disabled and isolated history storage.

    Its injected database resolver and clock make history windows deterministic.
    """
    monkeypatch.setattr(collector_module, "LMS_CANDIDATES", [])
    db_path = str(tmp_path / "history.db")
    database.init_db(db_path)
    app = create_app(
        collector=Collector(), db_path_resolver=lambda: db_path, clock=lambda: now,
    )
    with TestClient(app) as tc:
        yield tc


def test_history_default_range(client, seed, sample_prediction):
    r = client.get("/api/history")  # no query param -> default 1h
    assert r.status_code == 200
    body = r.json()
    assert body["range"] == "1h"
    assert body["generatedAt"] == "2026-08-15T10:30:00.000Z"
    assert body["series"] == []  # empty DB is a successful 200


def test_history_5m(client, seed, sample_prediction):
    seed(sample_prediction)  # exactly now: inside every window (closed end)
    r = client.get("/api/history?range=5m")
    assert r.status_code == 200
    body = r.json()
    assert body["range"] == "5m"
    assert len(body["series"]) == 1
    s = body["series"][0]
    assert s["model"] == "qwen3.8-27b-mlx"
    assert s["points"] == [{
        "timestamp": "2026-08-15T10:30:00.000Z",  # 30 s bucket (10:30:00 is aligned)
        "avgTokensPerSecond": 15.84,
        "count": 1,
    }]


def test_history_15m(client, seed, sample_prediction):
    seed(sample_prediction)
    r = client.get("/api/history?range=15m")
    assert r.status_code == 200
    assert r.json()["range"] == "15m"


def test_history_1h(client, seed, sample_prediction):
    seed(sample_prediction)
    r = client.get("/api/history?range=1h")
    assert r.status_code == 200
    body = r.json()
    assert body["range"] == "1h"
    assert body["series"][0]["points"] == [{
        "timestamp": "2026-08-15T10:30:00.000Z",  # minute bucket
        "avgTokensPerSecond": 15.84,
        "count": 1,
    }]


def test_history_24h(client, seed, sample_prediction):
    seed(sample_prediction)
    r = client.get("/api/history?range=24h")
    assert r.status_code == 200
    body = r.json()
    assert body["range"] == "24h"
    assert body["series"][0]["points"] == [{
        "timestamp": "2026-08-15T10:30:00.000Z",  # 15 min bucket
        "avgTokensPerSecond": 15.84,
        "count": 1,
    }]


def test_history_invalid_range(client):
    r = client.get("/api/history?range=10m")
    assert r.status_code == 400
    assert r.json() == {"error": "invalid range; expected one of: 5m, 15m, 1h, 24h, 1mo"}
    # empty range behaves as the default 1h
    r = client.get("/api/history?range=")
    assert r.status_code == 200
    assert r.json()["range"] == "1h"


def test_history_rejects_removed_1m_range(client):
    r = client.get("/api/history?range=1m")
    assert r.status_code == 400


def test_dashboard_returns_recent_history_and_summary(client, seed):
    seed({"modelIdentifier": "older", "tokensPerSecond": 5.0}, ts_offset_s=-2 * 3600)
    seed({"modelIdentifier": "alpha", "tokensPerSecond": 10.0,
          "promptTokensCount": 100, "predictedTokensCount": 25,
          "timeToFirstTokenSec": 1.5, "totalTimeSec": 4.0}, ts_offset_s=-30)
    seed({"modelIdentifier": "alpha", "tokensPerSecond": 20.0,
          "promptTokensCount": 200, "predictedTokensCount": 50,
          "timeToFirstTokenSec": 2.5, "totalTimeSec": 6.0})

    r = client.get("/api/dashboard?range=1h")

    assert r.status_code == 200
    body = r.json()
    assert body["range"] == "1h"
    assert body["start"] == "2026-08-15T09:30:00.000Z"
    assert body["end"] == "2026-08-15T10:30:00.000Z"
    assert [item["tokensPerSecond"] for item in body["recent"]] == [20.0, 10.0, 5.0]
    assert body["summary"] == [{
        "model": "alpha", "requests": 2, "avgTokensPerSecond": 15.0,
        "medianTokensPerSecond": 15.0, "minTokensPerSecond": 10.0,
        "maxTokensPerSecond": 20.0, "avgTimeToFirstTokenSec": 2.0,
        "promptTokens": 300, "outputTokens": 75,
    }]
    assert body["history"]["range"] == "1h"


def test_dashboard_accepts_custom_window_up_to_seven_days(client, seed, now):
    seed({"modelIdentifier": "alpha", "tokensPerSecond": 10.0}, ts_offset_s=-2 * 3600)
    start = "2026-08-15T08:30:00.000Z"
    end = "2026-08-15T10:30:00.000Z"
    r = client.get(f"/api/dashboard?start={start}&end={end}")

    assert r.status_code == 200
    assert r.json()["range"] == "custom"
    assert r.json()["start"] == start
    assert len(r.json()["recent"]) == 1


def test_dashboard_month_range_returns_the_last_ten_values_per_model(client, seed):
    for index in range(11):
        seed(
            {"modelIdentifier": "alpha", "tokensPerSecond": float(index)},
            ts_offset_s=-(11 - index) * 60,
        )

    r = client.get("/api/dashboard?range=1mo")

    assert r.status_code == 200
    body = r.json()
    assert body["range"] == body["history"]["range"] == "1mo"
    points = body["history"]["series"][0]["points"]
    assert [point["avgTokensPerSecond"] for point in points] == list(range(1, 11))


@pytest.mark.parametrize(
    "query",
    [
        "start=2026-08-01T10:30:00.000Z&end=2026-08-15T10:30:00.000Z",
        "start=2026-08-15T10:30:00.000Z",
        "end=2026-08-15T10:30:00.000Z",
    ],
)
def test_dashboard_rejects_invalid_custom_windows(client, query):
    r = client.get("/api/dashboard?" + query)
    assert r.status_code == 400


def test_history_empty(client):
    r = client.get("/api/history")
    assert r.status_code == 200
    body = r.json()
    assert body["series"] == []


def test_history_multiple_models(client, seed):
    a = {"modelIdentifier": "alpha", "tokensPerSecond": 10.0}
    b = {"modelIdentifier": "beta", "tokensPerSecond": 20.0}
    seed(a)  # same bucket on purpose: models must never mix
    seed(b)
    r = client.get("/api/history?range=1h")
    assert r.status_code == 200
    body = r.json()
    assert [s["model"] for s in body["series"]] == ["alpha", "beta"]
    assert [s["points"][0]["avgTokensPerSecond"] for s in body["series"]] == [10.0, 20.0]
    assert all(s["points"][0]["count"] == 1 for s in body["series"])


@pytest.fixture()
def seeded_client(monkeypatch, tmp_path, now, seed):
    """Client whose history DB is seeded before the app lifespan runs."""
    monkeypatch.setattr(collector_module, "LMS_CANDIDATES", [])
    db_path = str(tmp_path / "history.db")
    database.init_db(db_path)
    seed({"modelIdentifier": "old-model", "tokensPerSecond": 5.0}, ts_offset_s=-60)
    seed({"modelIdentifier": "new-model", "tokensPerSecond": 9.5})
    app = create_app(
        collector=Collector(), db_path_resolver=lambda: db_path, clock=lambda: now,
    )
    with TestClient(app) as tc:
        yield tc


def test_startup_loads_latest_from_db(seeded_client):
    c = seeded_client.app.state.collector
    assert c.prediction is not None  # latest row, not the older one
    assert c.prediction["modelIdentifier"] == "new-model"
    r = seeded_client.get("/api/state")
    assert r.status_code == 200
    body = r.json()
    assert body["prediction"]["modelIdentifier"] == "new-model"
    assert body["collector"] == "error"  # lms disabled in tests (v0.1 flow)


def test_startup_empty_db(client):
    c = client.app.state.collector
    assert c.prediction is None  # nothing stored yet; live view stays empty
    r = client.get("/api/state")
    assert r.status_code == 200
    body = r.json()
    assert body["prediction"] is None
    assert body["collector"] == "error"


def test_startup_then_live_event_replaces(seeded_client, tmp_path):
    c = seeded_client.app.state.collector

    line = json.dumps({
        "timestamp": 1786744900000,
        "data": {
            "type": PREDICTION_TYPE,
            "output": "live output",
            "stats": {"tokensPerSecond": 30.5},
            "modelIdentifier": "live-model",
        },
    }).encode()

    class FakeStream:
        def __init__(self, lines):
            self._lines = list(lines)

        async def readline(self):
            if self._lines:
                return self._lines.pop(0)
            return b""

    class FakeProc:
        def __init__(self, lines):
            self.stdout = FakeStream(lines)
            self.stderr = FakeStream([])
            self.returncode = 0

        async def wait(self):
            return 0

    db_path = str(tmp_path / "history.db")
    conn = database.connect(db_path)
    before = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
    conn.close()

    async def scenario():
        c.proc = FakeProc([line])
        await c._run()

    asyncio.run(scenario())

    assert c.prediction["modelIdentifier"] == "live-model"  # live event won
    conn = database.connect(db_path)
    after = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
    conn.close()
    assert after == before + 1  # the live event was persisted too


def test_startup_db_failure_degrades_to_memory_only(monkeypatch, tmp_path, now, capsys):
    """Database setup failure leaves the injected collector usable in memory."""
    monkeypatch.setattr(collector_module, "LMS_CANDIDATES", [])

    def unavailable(path):
        raise OSError("disk unavailable")

    monkeypatch.setattr(database, "init_db", unavailable)
    collector = Collector()
    app = create_app(
        collector=collector,
        db_path_resolver=lambda: str(tmp_path / "history.db"),
        clock=lambda: now,
    )
    with TestClient(app) as tc:
        assert collector.db_path is None
        response = tc.get("/api/state")
        assert response.status_code == 200
        assert response.json()["prediction"] is None
    assert "history database unavailable" in capsys.readouterr().err


def test_index_serves_frontend(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "LM SPEED VIEWER" in r.text
    assert 'href="/static/styles.css"' in r.text
    assert 'src="/static/app.js"' in r.text


def test_static_assets_are_served(client):
    styles = client.get("/static/styles.css")
    script = client.get("/static/app.js")

    assert styles.status_code == script.status_code == 200
    assert "text/css" in styles.headers["content-type"]
    assert "javascript" in script.headers["content-type"]
    assert ".app" in styles.text
    assert "new EventSource" in script.text


def test_api_state_reflects_collector(client):
    client.app.state.collector.prediction = {"modelIdentifier": "m", "tokensPerSecond": 1.0}
    r = client.get("/api/state")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"collector", "detail", "prediction"}
    # lms is disabled in tests, so lifespan start() took the error path
    assert body["collector"] == "error"
    assert body["prediction"]["modelIdentifier"] == "m"


def test_events_streams_snapshot_and_keepalive(monkeypatch):
    real_wait_for = asyncio.wait_for

    async def fast_wait_for(aw, timeout=None, *args, **kwargs):
        t = 0.01 if timeout is None else min(timeout, 0.01)
        return await real_wait_for(aw, t, *args, **kwargs)

    monkeypatch.setattr(asyncio, "wait_for", fast_wait_for)
    c = Collector()
    c.status, c.detail, c.prediction = "connected", "", {"modelIdentifier": "m"}
    c.subscribers.clear()

    async def scenario():
        request = Request({"type": "http", "method": "GET", "path": "/events"})
        app = create_app(collector=c)
        response = await app.state.events_handler(request)
        assert response.media_type == "text/event-stream"
        assert response.headers["cache-control"] == "no-cache"
        gen = response.body_iterator
        first = await gen.__anext__()
        assert len(c.subscribers) == 1
        data = json.loads(first[len("data: "):].strip())
        assert data["collector"] == "connected"
        c.publish()  # queued update for the subscriber
        second = await gen.__anext__()
        assert json.loads(second[len("data: "):].strip())["collector"] == "connected"
        third = await gen.__anext__()  # queue empty -> keepalive after timeout
        assert third == ": keepalive\n\n"
        await gen.aclose()
        assert len(c.subscribers) == 0

    asyncio.run(scenario())
