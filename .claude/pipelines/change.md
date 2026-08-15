# Change Pipeline

Use for non-trivial production changes, bugs, refactors, API/SSE changes,
persistence work, or dependency changes.

1. Read the relevant task file under `tasks/` when it defines the work; inspect
   affected code and tests.
2. For task-backed or user-requested branch work, run `work-with-git`.
3. Run `test-change` to add or plan the lowest-level useful coverage.
4. Run `implement-change` for the smallest complete change.
5. Run `validate-change`; include the coverage gate if `app.py` changed.
6. For medium/high risk, run `code-reviewer` in a fresh read-only context.
7. Update README or task documentation when observable behavior changed, then
   run `task-complete`.

Stop and return to the manager if acceptance criteria, a migration, security,
or external process control needs an unapproved decision.
