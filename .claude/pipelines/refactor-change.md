# Refactor Change Pipeline

## Trigger

Use for behavior-preserving refactors that change structure, names, module boundaries, or
implementation internals without changing product behavior, public contracts, canonical formats,
or persistence semantics.

## Conditional Gates

- Run `work-with-git` when the manager classifies the work as standard or major task-backed
  refactor work and states that fresh branch creation or task-state hygiene is required. Require
  `Skill: work-with-git - output below`.
- Run `spec-driven-development` unless an accepted specification already covers the behavior, or the
  manager's specification-materiality scan exempted the change. A public behavior or contract change
  leaves this route.
- Run `test-change` before implementation when existing coverage does not characterize the behavior
  being preserved, or to produce a coverage-review artifact explaining why no new characterization
  tests are needed.
- For independent review findings with Critical, High, or Major severity as defined in
  `.claude/conventions/review-severity.md`, repeat fix and re-review up to three times. Stop with
  blockers if those severities remain. Each loop returns to the responsible implementation, test,
  or documentation capability, reruns required validation, reruns the same reviewer, and records the
  attempt count plus repeated artifact labels.

## Ordered Steps

1. Run `work-with-git` when the conditional gates require it.
2. Run `spec-driven-development` only when the conditional gates require it. Require
   `Skill: spec-driven-development - output below` when run.
3. Run `test-change` for characterization, test-gap closure, or an explicit coverage review. Require
   `Skill: test-change - output below`.
4. Run `implement-change`. Require `Skill: implement-change - output below`.
5. Run `test-change` for post-refactor execution. Require `Skill: test-change - output below`.
6. Run `validate-change`. Require `Skill: validate-change - output below`.
7. Run `code-reviewer` when the manager classified risk as medium, high, or system-level. Require
   `Agent: code-reviewer - output below`.

Stop on a blocked or failed step and return control to the manager. The manager owns documentation
maintenance and task-complete after this pipeline.

## Output Contract

Begin with `Pipeline: refactor-change - output below` and report status, completed handoffs,
artifact labels, behavior-preservation evidence, skipped steps with reasons, review-loop attempt
count and repeated artifact labels, deviations, and blockers.
