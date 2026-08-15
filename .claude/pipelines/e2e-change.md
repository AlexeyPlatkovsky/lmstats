# E2E Change Pipeline

## Trigger

Use for creating, updating, or fixing TaskPilot functional Playwright E2E tests, Page Objects,
E2E support helpers, `data-test-id` hooks, or E2E CI behavior.

## Conditional Gates

- E2E is part of UI TDD. Before UI implementation for a major UI path, run `write-e2e-tests` in
  tests-first mode unless the test-level matrix proves component, API, or unit coverage is the
  smallest sufficient level.
- Every selected E2E row must explain why unit, component, or API tests cannot fully prove the
  workflow.
- Functional specs must use Page Objects; Page Objects own all Playwright locator construction.
- UI changes run the affected functional E2E scope after implementation. If no functional E2E is
  selected, validation must state the explicit lower-level reason.
- Run `e2e-test-reviewer` after implementation for any changed functional E2E spec, Page Object,
  E2E support helper, or selector policy.

## Ordered Steps

1. Run `test-change` for the test-level matrix. Require `Skill: test-change - output below`.
2. Run `write-e2e-tests`. Require `Skill: write-e2e-tests - output below`.
3. Run `test-change` for post-implementation execution. Require
   `Skill: test-change - output below`.
4. Run `e2e-test-reviewer`. Require `Agent: e2e-test-reviewer - output below`.
5. Run `validate-change`. Require `Skill: validate-change - output below`.

Stop on a blocked or failed step and return control to the manager. The manager owns documentation
maintenance and task-complete.

## Output Contract

Begin with `Pipeline: e2e-change - output below` and report status, completed handoffs, artifact
labels, E2E justification coverage, changed Page Objects, changed specs, changed `data-test-id`
hooks, commands and results, review-loop attempt count, deviations, and blockers.
