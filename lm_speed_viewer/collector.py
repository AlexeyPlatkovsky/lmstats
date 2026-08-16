"""Passive LM Studio log-stream collection and fan-out."""

import asyncio
import json
import os
import shutil
import sys
from contextlib import closing

from . import database
from .parser import parse_line


LMS_CANDIDATES = [shutil.which("lms"), os.path.expanduser("~/.lmstudio/bin/lms")]


class Collector:
    """Runs the lms log stream subprocess and tracks the latest prediction."""

    def __init__(self, db_path=None):
        self.status = "starting"
        self.detail = ""
        self.prediction = None
        self.proc = None
        self.db_path = db_path
        self._stopping = False
        self.subscribers = set()

    def snapshot(self):
        return {
            "collector": self.status,
            "detail": self.detail or None,
            "prediction": self.prediction,
        }

    def publish(self):
        payload = json.dumps(self.snapshot())
        for queue in list(self.subscribers):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                pass

    async def start(self):
        executable = next((candidate for candidate in LMS_CANDIDATES if candidate), None)
        if not executable:
            self.status = "error"
            self.detail = "lms CLI not found (checked PATH and ~/.lmstudio/bin)"
            self.publish()
            return
        try:
            self.proc = await asyncio.create_subprocess_exec(
                executable, "log", "stream", "--source", "model", "--filter", "output",
                "--stats", "--json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except OSError as error:
            self.status = "error"
            self.detail = f"failed to start lms: {error}"
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
            if not line:
                break
            prediction = parse_line(line.decode("utf-8", "replace"))
            if prediction is not None:
                self.prediction = prediction
                self._persist(prediction, line)
                self.publish()
        return_code = await proc.wait()
        if not self._stopping and self.status == "connected":
            self.status = "disconnected"
            self.detail = f"lms log stream exited (code {return_code})"
        self.publish()

    def _persist(self, prediction, raw_line):
        if self.db_path is None:
            return
        try:
            with closing(database.connect(self.db_path)) as conn:
                database.insert_prediction(conn, prediction, raw_line.decode("utf-8", "replace"))
        except Exception:
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
