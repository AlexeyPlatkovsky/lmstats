# AGENT.md — Working Rules for LM Speed Viewer

Read this before making any change. These rules apply to every stage of v0.2
and beyond.

## Project in one paragraph

Local web app (FastAPI + SSE, single `app.py` module) that passively observes
LM Studio: it runs `lms log stream --source model --filter output --stats
--json` as a child process, keeps the latest completed prediction in memory,
and pushes updates to browser tabs over SSE. Run with `python app.py` →
http://127.0.0.1:8765. Never proxy, restart, or configure LM Studio; never
kill or restart the `lms`/LM Studio processes from tests.

## Commands

```sh
pip install -r requirements-dev.txt   # runtime + test/lint deps (once)

python app.py                          # run the app
ruff check .                           # lint
pytest                                 # tests
pytest --cov=app --cov-report=term-missing --cov-fail-under=95   # tests + coverage gate
```

Coverage measures the application module (`app.py`) only. Do not inflate it:
no `coverage omit` tricks, no dummy tests that exist only to raise the number.

## Working rules

1. **TDD where practical.** Write or extend a test that expresses the desired
   behavior before changing code. For bug fixes, add a failing regression
   test first, then fix the bug.
2. **Run relevant tests after every significant piece of work** — not just at
   the end. Fix breakage immediately while context is fresh.
3. **Run lint regularly** (`ruff check .`). Keep new code lint-clean; do not
   disable rules to silence findings.
4. **Before declaring work complete**, run the full gate: lint + tests +
   coverage (all must pass, see Release gates below).
5. **UI changes:** verify meaningful UI changes with `playwright-cli` against
   the running app (http://127.0.0.1:8765) — load the page, check the changed
   element/behavior, capture evidence. Do not rely on code reading alone for
   UI work.
6. **Code review:** after implementation is complete, run the `code-reviewer`
   subagent (`.claude/agents/code-reviewer.md`) on the completed changes. Fix
   valid findings (all CRITICAL/HIGH; MEDIUM/LOW unless explicitly accepted
   with a reason) and rerun the affected checks.
7. **No unrelated scope expansion.** Do what the current task asks. No
   speculative abstractions, no drive-by refactors, no v0.2 features before
   their stage. If you notice an unrelated problem, note it in the summary
   instead of fixing it.

## Release gates

A stage (and v0.2 as a whole) is releasable only when all of these pass:

```text
lint: PASS                          ruff check .
tests: PASS                         pytest
coverage >= 95%: PASS               pytest --cov=app --cov-report=term-missing --cov-fail-under=95
playwright-cli verification: PASS   required for UI changes (N/A if no UI changed)
code-reviewer: PASS                 run after implementation; CRITICAL/HIGH findings fixed, MEDIUM/LOW addressed or explicitly accepted
```

Report the actual result of each gate in your final summary. Do not claim a
gate passed without running it.
