---
name: validate-change
description: Runs final read-only validation for a routed LM Stats Viewer change. Use after implementation to verify requirements, tests, lint, coverage, UI evidence, documentation, and diff scope.
---

# Validate Change

1. Read the request, acceptance criteria, changed files, tests, and final diff.
2. Run `ruff check .` and `pytest`. If `app.py` changed, also run
   `pytest --cov=app --cov-report=term-missing --cov-fail-under=95`.
3. For UI changes, require `playwright-cli` evidence or record the exact reason
   it is blocked; do not claim browser verification from code inspection.
4. Confirm the change preserves passive observation of LM Studio, handles
   relevant error paths, and does not add unapproved scope or dependencies.
5. Check README and task documentation for observable behavior or command drift.

Report each gate as pass, fail, skipped, or blocked with evidence. Overall pass
requires every applicable gate to pass.
