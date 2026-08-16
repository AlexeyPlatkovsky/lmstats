---
name: implement-change
description: Implements a scoped LM Speed Viewer code or documentation change after manager routing. Use inside a change or UI pipeline; it does not own final validation or review.
---

# Implement Change

1. Read the manager output, selected pipeline, relevant task under `tasks/`,
   affected code, and tests.
2. Restate the observable behavior and acceptance criteria. Stop for an
   unapproved API/SSE contract, persistence migration, dependency, security,
   or LM Studio-control change.
3. Confirm the focused test was written and failed before implementation, or
   record the justified exception. Implement the smallest complete change.
   Keep parser, collection, HTTP, and browser concerns separate; preserve
   malformed-input handling.
4. Add no speculative abstractions or unrelated cleanup.
5. Run focused checks after edits and inspect the diff for accidental churn.
6. Update README or task documentation only when facts the user sees changed.

Report changed files, behavior, checks, assumptions, and blockers. Return to
the pipeline for validation and review.
