---
name: work-with-git
description: Prepares TaskPilot work branches and canonical task state for routed non-trivial work without committing or pushing.
---

# Work With Git

Use only when the manager or pipeline requires work preparation. Do not commit, push, rewrite
history, discard changes, or run destructive Git commands unless the user explicitly requests it.

1. Inspect the current branch, upstream, and working tree.
2. Read the manager artifact for task backing, branch decision, branch source, branch name,
   task-state decision, target task item, sanctioned task-state update path, and required
   verification evidence. Stop if any required decision is missing.
3. If the manager requires a fresh branch, use the approved branch source from the manager artifact.
   Prefer an already available local ref such as `origin/main`. Do not fetch or otherwise require
   network access unless the user or manager explicitly approved it for this route. Block when the
   approved branch source is unavailable.
4. Use `feature/<task_id>-<slug>` for standard or major feature work with a task ID, and
   `refactor/<task_id>-<slug>` for standard or major task-backed behavior-preserving refactors with
   a task ID.
5. If no task ID exists or the change is small, report that branch creation or task movement is
   skipped unless the user asked for it.
6. When the manager requires task-state hygiene, move the exact target task item to `in_progress`
   only through the sanctioned update path named in the manager artifact. Prefer an implemented
   TaskPilot CLI or domain/service operation that writes the canonical file first. If the manager
   names direct canonical-file editing, first read the accepted canonical format docs/specs it
   cites, update only that canonical task file, and do not refresh any disposable index/cache until
   after the canonical write succeeds. Block instead of guessing the task file, update mechanism, or
   serialization rules.
7. Verify the canonical task file changed as required before any disposable index/cache refresh.
8. Preserve unrelated working-tree changes and stop if branch creation or task movement would
   overwrite them.

The artifact begins with `Skill: work-with-git - output below` and reports status, branch source,
branch name or skip reason, task-state action or skip reason, canonical-write verification,
working-tree assumptions, checks, and blockers.
