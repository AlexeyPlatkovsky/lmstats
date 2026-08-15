# Code Review Pipeline

## Trigger

Use for a read-only review of a diff, branch, commit, file set, or completed change.

## Ordered Steps

1. Run `code-reviewer`. Require `Agent: code-reviewer - output below`.
2. Run `validate-change` only when the review request includes verification or when existing
   validation evidence is missing. Require `Skill: validate-change - output below`.

Do not edit production files or tests. Stop on missing review scope or governing requirements. A
failed or blocked review returns control to the manager and does not advance to completion. The
manager owns task-complete.

## Output Contract

Begin with `Pipeline: code-review - output below` and report status, reviewed scope, artifact
labels, validation decision, and blockers.
