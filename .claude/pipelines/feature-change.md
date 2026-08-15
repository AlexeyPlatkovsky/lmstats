# Feature Change Pipeline

## Trigger

Use for a feature or non-trivial bug fix that changes TaskPilot production behavior.

## Conditional Gates

- Run `work-with-git` for standard or major task-backed feature work. The manager must require a
  fresh branch unless the user explicitly overrides it or branch creation is blocked. Require
  `Skill: work-with-git - output below`.
- Skip `work-with-git` for small low-risk changes unless the user requested branch or task-state
  handling.
- Require tests before implementation for behavior changes. If full test code before
  implementation is not feasible, step 3 must still produce a requirement→assertion mapping
  (a test plan) naming the specific assertion for every success path, error path, and boundary
  condition identified for the change. Boundary conditions include:
  - inputs the spec defines as invalid (→ must have a rejection assertion);
  - inputs the spec defines as out-of-scope (→ must have an explicit "documented limitation"
    entry or a rejection assertion);
  - silent-failure paths (files that can't be parsed, unreadable, wrong format);
  - error-envelope overlap with framework defaults (same status code, different body shape
    from the framework's own error handler).
  When step 3 operates in mapping-only mode (no test code), it explicitly overrides
  ``test-change`` SKILL.md step 6 — the skill produces a ``.claude/conventions/traceability.md``
  table (requirement rows, assertion columns) instead of executable tests. Full test code may be
  deferred to step 6, but the assertion mapping is a mandatory deliverable of step 3 and must be
  stored in the pipeline artifact.
- For major or high-risk feature work, run `code-reviewer` on the test scope before production
  implementation. Require `Agent: code-reviewer - output below`.
- For any `code-reviewer` findings with Critical, High, or Major severity as defined in
  `.claude/conventions/review-severity.md`, repeat fix and re-review up to three times. Stop with
  blockers if those severities remain. Each loop returns to the responsible implementation, test,
  or documentation capability, reruns required validation, reruns the same reviewer, and records the
  attempt count plus repeated artifact labels.

## Ordered Steps

1. Run `work-with-git` when the conditional gates require it.
2. Run `spec-driven-development` unless an accepted specification already covers the requested
   behavior, or the manager's specification-materiality scan exempted the change. Require
   `Skill: spec-driven-development - output below`.
3. Run `test-change` for tests-first coverage. Require `Skill: test-change - output below`.
4. Run `code-reviewer` on the test scope when the conditional gates require it. Require
   `Agent: code-reviewer - output below`.
5. Run `implement-change`. Require `Skill: implement-change - output below`.
6. Run `test-change` for post-implementation test execution and gaps. Require
   `Skill: test-change - output below`.
7. Run `validate-change`. Require `Skill: validate-change - output below`.
8. Run `code-reviewer` when the manager classified risk as medium, high, or system-level. Require
   `Agent: code-reviewer - output below`.

Stop on a blocked or failed step and return control to the manager. The manager owns documentation
maintenance and task-complete after this pipeline.

## Output Contract

Begin with `Pipeline: feature-change - output below` and report status, completed handoffs,
artifact labels, skipped steps with reasons — naming, when step 2 is skipped, the exempting clause
from the manager's specification-materiality scan and the documented behavior checked against it —
review-loop attempt count and repeated artifact
labels, deviations, and blockers.
