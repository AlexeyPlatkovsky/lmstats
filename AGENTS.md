# AGENTS.md — LM Speed Viewer

Read this file before changing the repository.

## Project

LM Speed Viewer is a local FastAPI + SSE app in `app.py`. It passively runs
`lms log stream --source model --filter output --stats --json`, keeps the latest
completed prediction in memory, and serves `http://127.0.0.1:8765`.

v0.2 adds SQLite persistence of all predictions and a historical speed graph
UI. The database is located at `~/.lmstudio-speed-viewer/history.db` by default
(overridable via `LM_SPEED_VIEWER_DB`). The app resolves `db.default_db_path()`
at lifespan startup (not import time) so tests can monkeypatch it per-request.

Agents may start and stop `python app.py` for local verification. The viewer's
normal passive log-stream lifecycle is permitted. Never directly proxy,
restart, configure, kill, or otherwise control LM Studio or `lms`, including
independently managing the viewer's `lms` child process. Automated tests must
not affect those processes.

## Commands

```sh
pip install -r requirements-dev.txt
python app.py
ruff check .
pytest
pytest --cov=lm_speed_viewer --cov-report=term-missing --cov-fail-under=95
```

## Operating model

1. Treat a request as non-trivial if it changes behavior, an API/SSE contract,
   persistence, UI, architecture, dependencies, instructions, or needs several
   coordinated steps.
2. Before non-trivial work, read `.claude/skills/manager/SKILL.md` and follow
   its selected route. Do not bypass the manager or invent a parallel workflow.
3. TDD is the primary approach for every significant feature, bug fix, or
   refactor: first add a focused test that fails for the intended behavior,
   then implement the smallest passing change. Record any exception when a
   meaningful automated test cannot be written first. For bugs, that first
   test is a regression test.
4. Preserve unrelated work. Do not reset, force-push, or commit/push unless the
   user explicitly asks.
5. Run the relevant test/lint checks after meaningful edits. Keep code simple;
   do not add speculative abstractions or coverage-only tests.
6. UI changes require a live browser check against `http://127.0.0.1:8765`.
   Use `.claude/skills/playwright-cli/SKILL.md` when the available runtime has
   browser automation; otherwise report that evidence as blocked.
7. After non-trivial implementation, use `.claude/agents/code-reviewer.md` in a
   fresh read-only pass when subagents are available. If not, perform that same
   checklist separately before completion.
8. Use `.taskpilot/` only through the `taskpilot` CLI and
   `.claude/skills/taskpilot-cli/SKILL.md`. Track work only when the user asks
   or the manager says the work is task-backed.

## Completion gates

Before calling work complete, report the checks actually run:

- `ruff check .`
- `pytest`
- coverage gate above when `app.py` changed
- browser evidence for UI changes (otherwise N/A)
- code-review result for non-trivial implementation

Do not claim a gate passed unless it ran and passed.
