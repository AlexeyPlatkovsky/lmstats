---
name: task-complete
description: Closes a routed LM Speed Viewer task by checking planned work, evidence, documentation, and required release gates. Use as the final step of a non-trivial pipeline.
---

# Complete Task

1. Confirm every selected handoff completed or was explicitly skipped.
2. Inspect the final diff for unrelated changes and verify documentation is
   current where behavior, commands, or limitations changed.
3. Report the actual status of lint, tests, coverage (when `app.py` changed),
   browser verification (for UI), and review (for non-trivial implementation).
4. If work is tied to a user-supplied TaskPilot ID, use `taskpilot-cli` to move
   it only when the user requested status tracking or the manager required it.
5. Do not commit, push, or create a TaskPilot item without explicit request.

State completed scope, changed files, gate results, remaining risks, and any
blocker. Never mark completion when a required gate failed or is blocked.
