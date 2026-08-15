---
name: test-change
description: Designs, adds, or runs focused LM Speed Viewer tests for routed behavior changes. Use before implementation where practical and after implementation to prove parser, collector, API, or SSE behavior.
---

# Test Change

1. Read the request, relevant task, affected tests, and `app.py` behavior.
2. Map each acceptance criterion to the lowest useful level: parser unit test,
   collector/state test, FastAPI API test, or browser check. Do not use browser
   automation when a lower-level test proves the behavior.
3. For a bug, add a failing regression test before the fix where practical.
4. Cover malformed input, missing fields, subprocess errors, and concurrency
   boundaries when they are relevant. Never start or kill LM Studio or `lms`.
5. Run the narrow tests after edits, then `pytest` when the pipeline requires
   it. Keep tests behavior-focused; do not add tests solely to raise coverage.

Report the criterion-to-test mapping, changed tests, commands/results, gaps,
and blockers.
