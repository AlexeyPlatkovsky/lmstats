#!/usr/bin/env python3
"""LM Speed Viewer v0.1

Passive observer for LM Studio: runs `lms log stream --source model
--filter output --stats --json` as a child process, keeps the latest
completed prediction in memory, and shows it in the browser via SSE.

Run: python app.py  ->  http://127.0.0.1:8765
"""

import asyncio
import json
import os
import shutil
import sys
from contextlib import asynccontextmanager, closing
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

import db

HOST = "127.0.0.1"
PORT = 8765

LMS_CANDIDATES = [shutil.which("lms"), os.path.expanduser("~/.lmstudio/bin/lms")]
PREDICTION_TYPE = "llm.prediction.output"

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


def parse_line(line):
    """Parse one line of `lms log stream --json` output.

    Returns a normalized dict for a valid completed prediction event,
    or None if the line is malformed JSON or an unrelated event.
    Missing optional fields become None (rendered as "—" in the UI).
    """
    line = line.strip()
    if not line:
        return None
    try:
        obj = json.loads(line)
    except ValueError:
        return None
    if not isinstance(obj, dict):
        return None
    data = obj.get("data")
    if not isinstance(data, dict) or data.get("type") != PREDICTION_TYPE:
        return None

    stats = data.get("stats")
    if not isinstance(stats, dict):
        stats = {}

    def num(key):
        v = stats.get(key)
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return None
        return v

    model = data.get("modelIdentifier")
    ts = obj.get("timestamp")
    stop_reason = stats.get("stopReason")
    output = data.get("output")
    return {
        "modelIdentifier": model if isinstance(model, str) and model else None,
        "tokensPerSecond": num("tokensPerSecond"),
        "timeToFirstTokenSec": num("timeToFirstTokenSec"),
        "totalTimeSec": num("totalTimeSec"),
        "promptTokensCount": num("promptTokensCount"),
        "predictedTokensCount": num("predictedTokensCount"),
        "totalTokensCount": num("totalTokensCount"),
        "timestampMs": ts if isinstance(ts, (int, float)) and not isinstance(ts, bool) else None,
        "stopReason": stop_reason if isinstance(stop_reason, str) else None,
        "output": output if isinstance(output, str) else None,
    }


class Collector:
    """Runs the lms log stream subprocess and tracks the latest prediction."""

    def __init__(self, db_path=None):
        self.status = "starting"  # starting | connected | disconnected | error
        self.detail = ""
        self.prediction = None
        self.proc = None
        self.db_path = db_path  # SQLite path; None disables persistence
        self._stopping = False
        self.subscribers = set()  # one asyncio.Queue per SSE client

    def snapshot(self):
        return {
            "collector": self.status,
            "detail": self.detail or None,
            "prediction": self.prediction,
        }

    def publish(self):
        payload = json.dumps(self.snapshot())
        for q in list(self.subscribers):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                pass  # slow client drops the update; EventSource reconnects

    async def start(self):
        exe = next((c for c in LMS_CANDIDATES if c), None)
        if not exe:
            self.status = "error"
            self.detail = "lms CLI not found (checked PATH and ~/.lmstudio/bin)"
            self.publish()
            return
        try:
            self.proc = await asyncio.create_subprocess_exec(
                exe, "log", "stream", "--source", "model", "--filter", "output",
                "--stats", "--json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except OSError as e:
            self.status = "error"
            self.detail = f"failed to start lms: {e}"
            self.publish()
            return
        self.status = "connected"
        self.detail = ""
        self.publish()
        asyncio.create_task(self._run())

    async def _run(self):
        proc = self.proc
        asyncio.create_task(self._drain_stderr(proc))
        while True:
            line = await proc.stdout.readline()
            if not line:  # EOF: subprocess closed stdout and exited
                break
            pred = parse_line(line.decode("utf-8", "replace"))
            if pred is not None:
                self.prediction = pred
                self._persist(pred, line)
                self.publish()
        rc = await proc.wait()
        if not self._stopping and self.status == "connected":
            self.status = "disconnected"
            self.detail = f"lms log stream exited (code {rc})"
        self.publish()

    def _persist(self, pred, raw_line):
        if self.db_path is None:
            return
        try:
            with closing(db.connect(self.db_path)) as conn:
                db.insert_prediction(conn, pred, raw_line.decode("utf-8", "replace"))
        except Exception:  # persistence failure must not break live view
            print(f"failed to persist prediction: {sys.exc_info()[1]}", file=sys.stderr)

    async def _drain_stderr(self, proc):
        tail = []
        while True:
            line = await proc.stderr.readline()
            if not line:
                break
            text = line.decode("utf-8", "replace").strip()
            if text:
                tail.append(text)
                if len(tail) > 5:
                    tail.pop(0)
        self._stderr_tail = tail

    async def stop(self):
        self._stopping = True
        proc, self.proc = self.proc, None
        if proc is not None and proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                proc.kill()


collector = Collector()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@asynccontextmanager
async def lifespan(app):
    # Resolve the path at startup (never at import time) so tests can monkeypatch it.
    db_path = db.default_db_path()
    try:
        db.init_db(db_path)
        with closing(db.connect(db_path)) as conn:
            collector.prediction = db.latest_prediction(conn)
        collector.db_path = db_path
    except Exception as exc:  # persistence must never break the live view
        print(f"history database unavailable: {exc}", file=sys.stderr)
    await collector.start()
    yield
    await collector.stop()


app = FastAPI(title="LM Speed Viewer", lifespan=lifespan)


@app.get("/")
async def index(response: Response):
    resp = FileResponse(os.path.join(STATIC_DIR, "index.html"))
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


@app.get("/api/state")
async def api_state():
    return JSONResponse(collector.snapshot())


@app.get("/api/history")
async def api_history(range: str = ""):
    if range == "":
        range_key = "1h"  # omitted or empty -> default
    elif range in db.RANGE_DURATIONS:
        range_key = range
    else:
        return JSONResponse(
            {"error": "invalid range; expected one of: 5m, 15m, 1h, 24h"}, status_code=400)
    # Resolved per request (never at import time) so tests can monkeypatch it.
    path = db.default_db_path()
    return JSONResponse(db.get_history(path, range_key, now=_utcnow()))


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


@app.get("/api/dashboard")
async def api_dashboard(
    range: str = "1h", start: str = "", end: str = "", at: str = "",
):
    """Dashboard data for a fixed range or a user-selected window up to seven days."""
    now = _utcnow()
    if bool(start) != bool(end) or (at and (start or end)):
        return JSONResponse(
            {"error": "start and end must be provided together"}, status_code=400)
    if start and end:
        try:
            window_start = _parse_utc(start)
            window_end = _parse_utc(end)
        except ValueError:
            return JSONResponse({"error": "invalid ISO-8601 timestamp"}, status_code=400)
        if window_end <= window_start:
            return JSONResponse({"error": "end must be after start"}, status_code=400)
        if window_end - window_start > db.MAX_DASHBOARD_WINDOW:
            return JSONResponse({"error": "custom range cannot exceed seven days"}, status_code=400)
        if window_end > now:
            return JSONResponse({"error": "end cannot be in the future"}, status_code=400)
        range_key = "custom"
    else:
        range_key = range or "1h"
        if range_key not in db.RANGE_DURATIONS:
            return JSONResponse(
                {"error": "invalid range; expected one of: 5m, 15m, 1h, 24h"},
                status_code=400,
            )
        if at:
            try:
                window_end = _parse_utc(at)
            except ValueError:
                return JSONResponse({"error": "invalid ISO-8601 timestamp"}, status_code=400)
            if window_end > now:
                return JSONResponse({"error": "end cannot be in the future"}, status_code=400)
        else:
            window_end = now
        window_start = now - timedelta(seconds=db.RANGE_DURATIONS[range_key])
        if at:
            window_start = window_end - timedelta(seconds=db.RANGE_DURATIONS[range_key])
    path = db.default_db_path()
    return JSONResponse(db.get_dashboard(path, window_start, window_end, range_key))


@app.get("/events")
async def events(request: Request):
    async def gen():
        q = asyncio.Queue(maxsize=100)
        collector.subscribers.add(q)
        try:
            yield f"data: {json.dumps(collector.snapshot())}\n\n"
            while True:
                try:
                    payload = await asyncio.wait_for(q.get(), timeout=15)
                    yield f"data: {payload}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            collector.subscribers.discard(q)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT, log_level="warning", timeout_graceful_shutdown=5)
