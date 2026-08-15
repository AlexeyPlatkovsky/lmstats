---
name: work-with-git
description: Safely prepares a branch for manager-routed LM Speed Viewer work. Use only when the manager or user requires branch discipline; never commits, pushes, resets, or discards changes.
---

# Work With Git

1. Inspect branch, status, and available local refs.
2. Preserve unrelated changes. Stop if branch creation would overwrite or hide
   them.
3. Create a branch only when requested by the manager/user. Prefer
   `feature/<task-id>-<slug>` or `fix/<task-id>-<slug>` when a task ID exists.
4. Do not fetch, commit, push, rebase, reset, or force operations unless the
   user explicitly asks.
5. Report starting branch, created branch or skip reason, working-tree state,
   and blockers.
