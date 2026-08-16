"""FastAPI application factory and HTTP/SSE routes."""

import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager, closing
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import database
from .collector import Collector


STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


def utcnow() -> datetime:
    """Return the current aware UTC time."""
    return datetime.now(timezone.utc)


def parse_utc(value: str) -> datetime:
    """Parse an ISO-8601 timestamp with an explicit timezone."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def create_app(*, collector=None, db_path_resolver=None, clock=None, static_dir=None) -> FastAPI:
    """Create an isolated LM Speed Viewer application instance."""
    runtime_collector = collector or Collector()
    def path_resolver():
        if db_path_resolver is not None:
            return db_path_resolver()
        return database.default_db_path()

    runtime_clock = clock or utcnow
    frontend_dir = static_dir or STATIC_DIR

    @asynccontextmanager
    async def lifespan(app):
        path = app.state.db_path_resolver()
        try:
            database.init_db(path)
            with closing(database.connect(path)) as conn:
                app.state.collector.prediction = database.latest_prediction(conn)
            app.state.collector.db_path = path
        except Exception as error:
            print(f"history database unavailable: {error}", file=sys.stderr)
        await app.state.collector.start()
        yield
        await app.state.collector.stop()

    app = FastAPI(title="LM Speed Viewer", lifespan=lifespan)
    app.state.collector = runtime_collector
    app.state.db_path_resolver = path_resolver
    app.state.clock = runtime_clock
    app.state.static_dir = frontend_dir
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    async def index(response: Response):
        result = FileResponse(os.path.join(app.state.static_dir, "index.html"))
        result.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        result.headers["Pragma"] = "no-cache"
        result.headers["Expires"] = "0"
        return result

    @app.get("/api/state")
    async def api_state():
        return JSONResponse(app.state.collector.snapshot())

    @app.get("/api/history")
    async def api_history(range: str = ""):
        if range == "":
            range_key = "1h"
        elif range in database.RANGE_DURATIONS:
            range_key = range
        else:
            return JSONResponse(
                {"error": "invalid range; expected one of: 5m, 15m, 1h, 24h, 1mo"},
                status_code=400,
            )
        return JSONResponse(
            database.get_history(
                app.state.db_path_resolver(), range_key, now=app.state.clock(),
            )
        )

    @app.get("/api/dashboard")
    async def api_dashboard(range: str = "1h", start: str = "", end: str = "", at: str = ""):
        """Return dashboard data for a fixed range or a custom window up to seven days."""
        now = app.state.clock()
        if bool(start) != bool(end) or (at and (start or end)):
            return JSONResponse(
                {"error": "start and end must be provided together"}, status_code=400,
            )
        if start and end:
            try:
                window_start = parse_utc(start)
                window_end = parse_utc(end)
            except ValueError:
                return JSONResponse({"error": "invalid ISO-8601 timestamp"}, status_code=400)
            if window_end <= window_start:
                return JSONResponse({"error": "end must be after start"}, status_code=400)
            if window_end - window_start > database.MAX_DASHBOARD_WINDOW:
                return JSONResponse(
                    {"error": "custom range cannot exceed seven days"}, status_code=400,
                )
            if window_end > now:
                return JSONResponse({"error": "end cannot be in the future"}, status_code=400)
            range_key = "custom"
        else:
            range_key = range or "1h"
            if range_key not in database.RANGE_DURATIONS:
                return JSONResponse(
                    {"error": "invalid range; expected one of: 5m, 15m, 1h, 24h, 1mo"},
                    status_code=400,
                )
            if at:
                try:
                    window_end = parse_utc(at)
                except ValueError:
                    return JSONResponse(
                        {"error": "invalid ISO-8601 timestamp"}, status_code=400,
                    )
                if window_end > now:
                    return JSONResponse({"error": "end cannot be in the future"}, status_code=400)
            else:
                window_end = now
            window_start = now - timedelta(seconds=database.RANGE_DURATIONS[range_key])
            if at:
                window_start = window_end - timedelta(seconds=database.RANGE_DURATIONS[range_key])
        return JSONResponse(
            database.get_dashboard(
                app.state.db_path_resolver(), window_start, window_end, range_key,
            )
        )

    @app.get("/events")
    async def events(request: Request):
        async def gen():
            queue = asyncio.Queue(maxsize=100)
            app.state.collector.subscribers.add(queue)
            try:
                yield f"data: {json.dumps(app.state.collector.snapshot())}\n\n"
                while True:
                    try:
                        payload = await asyncio.wait_for(queue.get(), timeout=15)
                        yield f"data: {payload}\n\n"
                    except asyncio.TimeoutError:
                        yield ": keepalive\n\n"
            finally:
                app.state.collector.subscribers.discard(queue)

        return StreamingResponse(
            gen(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    app.state.index_handler = index
    app.state.api_state_handler = api_state
    app.state.api_history_handler = api_history
    app.state.api_dashboard_handler = api_dashboard
    app.state.events_handler = events
    return app
