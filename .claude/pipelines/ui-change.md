# UI Change Pipeline

## Trigger

Use for TaskPilot product UI design or implementation, including existing-page changes, local WebUI
component-library work, list/detail, forms, validation states, Kanban, tree, accessibility,
responsive behavior, and visual-system changes.

## Conditional Gates

- Product UI implementation follows the feature pipeline's conditional rigor for branch, task,
  tests-first, validation, and review gates when behavior changes.
- Local WebUI component-library work follows `.claude/conventions/ui-component-library.md`.
- Component coverage is required for changed React behavior, using the testing standard in
  `.claude/conventions/testing.md`.
- Functional E2E coverage for major UI paths and browser contract coverage for style/token/browser
  behavior are governed by `.claude/conventions/testing.md`. These are separate levels; do not use
  token, computed-style, screenshot-only, or visual-contract checks as functional E2E evidence.
- For independent review findings with Critical, High, or Major severity as defined in
  `.claude/conventions/review-severity.md`, repeat fix and re-review up to three times. Stop with
  blockers if those severities remain. Each loop returns to the responsible design,
  implementation, test, or documentation capability, reruns required validation, reruns the same
  reviewer, and records the attempt count plus repeated artifact labels.

## Ordered Steps

1. Run `work-with-git` when the conditional gates require it.
2. Run `spec-driven-development` unless an accepted specification already covers the requested
   behavior, or the manager's specification-materiality scan exempted the change. Require
   `Skill: spec-driven-development - output below`.
3. Run `design-ui`; create or update `designs/design.md`. Require
   `Skill: design-ui - output below`.
4. When implementation is requested, run `test-change` for tests-first coverage. Require
   `Skill: test-change - output below`.
5. When implementation is requested, run `implement-change`. Require
   `Skill: implement-change - output below`.
6. When implementation is requested, run `test-change` for post-implementation execution. Require
   `Skill: test-change - output below`.
7. Run `validate-change`, including committed Playwright TypeScript functional E2E evidence for
   major UI paths, separate browser contract evidence for style/token/browser behavior when
   required, and an explicit browser-evidence N/A reason when component-level evidence is
   sufficient. Require
   `Skill: validate-change - output below`.
8. Run `design-reviewer` in isolated fresh context. Require
   `Agent: design-reviewer - output below`.
9. Run `code-reviewer` when the manager classified risk as medium, high, or system-level, or when
   the UI change touches API/domain contracts. Require `Agent: code-reviewer - output below`.

Stop on a blocked or failed step and return control to the manager. The manager owns documentation
maintenance and task-complete.

## Output Contract

Begin with `Pipeline: ui-change - output below` and report status, design-system path, completed
handoffs, artifact labels, component coverage, functional E2E evidence, browser contract evidence,
skipped implementation steps, the exempting clause from the manager's specification-materiality scan
and the documented behavior checked against it whenever step 2 is skipped, review-loop attempt count
and repeated artifact labels, blockers, and whether the change affected reusable local components,
page-only composition, design tokens, or local docs.
