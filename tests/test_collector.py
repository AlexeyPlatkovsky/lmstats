"""Tests for the lms log stream collector: subprocess lifecycle and pub/sub."""

import asyncio
import contextlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import db  # noqa: E402

from lm_speed_viewer import collector as collector_module  # noqa: E402
from lm_speed_viewer.collector import Collector  # noqa: E402
from lm_speed_viewer.parser import PREDICTION_TYPE  # noqa: E402

PREDICTION_LINE = json.dumps({
    "timestamp": 1786744778242,
    "data": {
        "type": PREDICTION_TYPE,
        "output": "fixture output",
        "stats": {"tokensPerSecond": 12.5, "promptTokensCount": 10},
        "modelIdentifier": "test-model",
    },
}).encode()

OTHER_EVENT_LINE = json.dumps({
    "timestamp": 2,
    "data": {"type": "llm.prediction.input", "input": "x"},
}).encode()


class FakeStream:
    """Async readline() source over a fixed list of byte lines."""

    def __init__(self, lines=(), block_on_eof=False):
        self._lines = list(lines)
        self.block_on_eof = block_on_eof

    async def readline(self):
        if self._lines:
            return self._lines.pop(0)
        if self.block_on_eof:
            await asyncio.Event().wait()  # never returns; cancelled on loop close
        return b""


class FakeProc:
    """Stands in for asyncio.subprocess.Process."""

    def __init__(self, stdout_lines=(), stderr_lines=(), returncode=None,
                 wait_hang=False, stdout_block_on_eof=False):
        self.stdout = FakeStream(stdout_lines, block_on_eof=stdout_block_on_eof)
        self.stderr = FakeStream(stderr_lines)
        self.returncode = returncode
        self.wait_hang = wait_hang
        self.terminated = False
        self.killed = False

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.killed = True

    async def wait(self):
        if self.wait_hang:
            await asyncio.Event().wait()  # never exits on its own
        await asyncio.sleep(0)
        if self.returncode is None:
            return 143 if self.terminated else 0
        return self.returncode


def run(coro):
    """Run a coroutine to completion in a fresh event loop."""
    return asyncio.run(coro)


def test_snapshot_shape():
    c = Collector()
    assert c.snapshot() == {"collector": "starting", "detail": None, "prediction": None}
    c.detail = "some detail"
    c.prediction = {"modelIdentifier": "m"}
    assert c.snapshot() == {
        "collector": "starting",
        "detail": "some detail",
        "prediction": {"modelIdentifier": "m"},
    }


def test_publish_delivers_snapshot_to_subscribers():
    c = Collector()
    q = asyncio.Queue(maxsize=10)
    c.subscribers.add(q)
    c.publish()
    assert json.loads(q.get_nowait()) == c.snapshot()


def test_publish_ignores_full_queue():
    c = Collector()
    q = asyncio.Queue(maxsize=1)
    q.put_nowait("existing")
    c.subscribers.add(q)
    c.publish()  # must not raise; a slow client drops the update
    assert q.qsize() == 1


def test_start_when_lms_not_found(monkeypatch):
    monkeypatch.setattr(collector_module, "LMS_CANDIDATES", [])

    async def scenario():
        c = Collector()
        q = asyncio.Queue(maxsize=10)
        c.subscribers.add(q)
        await c.start()
        assert c.status == "error"
        assert "not found" in c.detail
        assert c.proc is None
        payload = json.loads(q.get_nowait())
        assert payload["collector"] == "error"

    run(scenario())


def test_start_when_spawn_fails(monkeypatch):
    monkeypatch.setattr(collector_module, "LMS_CANDIDATES", ["/fake/lms"])

    async def fake_exec(*args, **kwargs):
        raise OSError("boom")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)

    async def scenario():
        c = Collector()
        await c.start()
        assert c.status == "error"
        assert c.detail == "failed to start lms: boom"

    run(scenario())


def test_start_success(monkeypatch):
    monkeypatch.setattr(collector_module, "LMS_CANDIDATES", ["/fake/lms"])
    proc = FakeProc(stdout_lines=(), stdout_block_on_eof=True)  # stream stays open

    async def fake_exec(*args, **kwargs):
        return proc

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)

    async def scenario():
        c = Collector()
        await c.start()
        assert c.status == "connected"
        assert c.detail == ""
        assert c.proc is proc

    run(scenario())


def test_run_updates_prediction_and_disconnects():
    async def scenario():
        c = Collector()
        c.status = "connected"
        proc = FakeProc(
            stdout_lines=[PREDICTION_LINE, b"not json\n", OTHER_EVENT_LINE],
            returncode=0,
        )
        c.proc = proc
        q = asyncio.Queue(maxsize=10)
        c.subscribers.add(q)
        await c._run()
        assert c.prediction is not None
        assert c.prediction["modelIdentifier"] == "test-model"
        assert c.status == "disconnected"
        assert c.detail == "lms log stream exited (code 0)"
        payload = json.loads(q.get_nowait())
        assert payload["prediction"]["modelIdentifier"] == "test-model"

    run(scenario())


def test_run_while_stopping_keeps_status():
    async def scenario():
        c = Collector()
        c.status = "connected"
        c._stopping = True
        proc = FakeProc(stdout_lines=(), returncode=1)
        c.proc = proc
        q = asyncio.Queue(maxsize=10)
        c.subscribers.add(q)
        await c._run()
        assert c.status == "connected"  # shutdown in progress: no state flip
        assert c.detail == ""
        q.get_nowait()  # the final publish still happens

    run(scenario())


def test_run_when_not_connected_keeps_status():
    async def scenario():
        c = Collector()  # status "starting"
        proc = FakeProc(stdout_lines=(), returncode=1)
        c.proc = proc
        await c._run()
        assert c.status == "starting"

    run(scenario())


def test_drain_stderr_keeps_tail():
    async def scenario():
        c = Collector()
        proc = FakeProc(stderr_lines=[b"a\n", b"b\n", b"\n", b"c\n"])
        await c._drain_stderr(proc)
        assert c._stderr_tail == ["a", "b", "c"]

    run(scenario())


def test_drain_stderr_keeps_last_five():
    async def scenario():
        c = Collector()
        lines = [f"line{i}\n".encode() for i in range(7)]
        proc = FakeProc(stderr_lines=lines)
        await c._drain_stderr(proc)
        assert c._stderr_tail == [f"line{i}" for i in range(2, 7)]

    run(scenario())


def test_stop_without_proc():
    async def scenario():
        c = Collector()
        await c.stop()
        assert c._stopping is True

    run(scenario())


def test_stop_when_proc_already_exited():
    async def scenario():
        c = Collector()
        proc = FakeProc(returncode=0)
        c.proc = proc
        await c.stop()
        assert c.proc is None
        assert not proc.terminated and not proc.killed

    run(scenario())


def test_stop_terminates_and_waits():
    async def scenario():
        c = Collector()
        proc = FakeProc(returncode=None)  # exits right after terminate
        c.proc = proc
        await c.stop()
        assert proc.terminated and not proc.killed

    run(scenario())


def test_stop_kills_on_timeout(monkeypatch):
    real_wait_for = asyncio.wait_for

    async def fast_wait_for(aw, timeout=None, *args, **kwargs):
        t = 0.01 if timeout is None else min(timeout, 0.01)
        return await real_wait_for(aw, t, *args, **kwargs)

    monkeypatch.setattr(asyncio, "wait_for", fast_wait_for)

    async def scenario():
        c = Collector()
        proc = FakeProc(returncode=None, wait_hang=True)  # ignores terminate
        c.proc = proc
        await c.stop()
        assert proc.terminated and proc.killed

    run(scenario())


def test_persist_inserts_each_prediction(tmp_path):
    path = str(tmp_path / "history.db")
    db.init_db(path)

    async def scenario():
        c = Collector(db_path=path)
        proc = FakeProc(stdout_lines=[PREDICTION_LINE])
        c.proc = proc
        await c._run()

    run(scenario())

    conn = db.connect(path)
    try:
        rows = conn.execute("SELECT model, tokens_per_second FROM predictions").fetchall()
    finally:
        conn.close()
    assert len(rows) == 1
    assert rows[0]["model"] == "test-model"
    assert rows[0]["tokens_per_second"] == 12.5


def test_persist_failure_does_not_break_live_view(tmp_path, monkeypatch, capsys):
    path = str(tmp_path / "history.db")
    db.init_db(path)

    def boom(conn, pred, raw_line):
        raise RuntimeError("disk on fire")

    monkeypatch.setattr(db, "insert_prediction", boom)

    async def scenario():
        c = Collector(db_path=path)
        c.status = "connected"
        proc = FakeProc(stdout_lines=[PREDICTION_LINE], stdout_block_on_eof=True)
        c.proc = proc
        q = asyncio.Queue(maxsize=10)
        c.subscribers.add(q)
        task = asyncio.create_task(c._run())
        await q.get()
        assert c.prediction["modelIdentifier"] == "test-model"
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    run(scenario())

    err = capsys.readouterr().err
    assert "failed to persist prediction" in err
