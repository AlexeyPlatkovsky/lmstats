"""Tests for the HTTP routes and the SSE endpoint."""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app as app_module  # noqa: E402
from starlette.requests import Request  # noqa: E402


@pytest.fixture()
def client(monkeypatch):
    """TestClient with the lms CLI disabled so no real process is spawned."""
    monkeypatch.setattr(app_module, "LMS_CANDIDATES", [])
    c = app_module.collector
    c.status, c.detail, c.prediction, c.proc, c._stopping = (
        "starting", "", None, None, False)
    c.subscribers.clear()
    with TestClient(app_module.app) as tc:
        yield tc


def test_index_serves_frontend(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "LM SPEED VIEWER" in r.text


def test_api_state_reflects_collector(client):
    app_module.collector.prediction = {"modelIdentifier": "m", "tokensPerSecond": 1.0}
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
    c = app_module.collector
    c.status, c.detail, c.prediction = "connected", "", {"modelIdentifier": "m"}
    c.subscribers.clear()

    async def scenario():
        request = Request({"type": "http", "method": "GET", "path": "/events"})
        response = await app_module.events(request)
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
