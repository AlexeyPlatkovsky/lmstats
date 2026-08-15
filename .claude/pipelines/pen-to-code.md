# Pencil-to-Code Pipeline

## Trigger

Use when converting an accepted Pencil design to tested React code. Requires:
- a `.pen` file in `designs/` — stop if absent;
- an accepted spec in `docs/specs/` or explicit acceptance criteria supplied by the user — stop if absent.

## Risk Level

Use the risk classification from the manager artifact. If no manager artifact is present,
treat risk as medium. Conditional gates in stages 4 and 9 apply based on this classification.

## Ordered Steps

1. **Branch.** Run `work-with-git` unless the manager explicitly skipped it.
   Require: `Skill: work-with-git - output below`.

2. **Design translation.** Run `pen-to-code` skill to read the `.pen` frame and produce a component
   specification (props, states, layout token assignments, accessibility contract, test targets).
   The skill reads the design; it does not write code.
   Require: `Skill: pen-to-code - output below`. Stop if skill reports a blocker (missing required
   state, token gap, absent `.pen` file).

3. **Tests-first.** Run `test-change` to write component tests from the spec produced in stage 2.
   Require: `Skill: test-change - output below`.

4. **Test-scope review.** Run `code-reviewer` on test scope when risk is major or high.
   Require: `Agent: code-reviewer - output below`.
   - Critical, High, or Major findings → fix tests, re-run `test-change`, re-run `code-reviewer`.
     Up to 3 loops. Record loop count and repeat artifact labels.
   - If Critical, High, or Major findings remain after 3 loops, stop with blockers.

5. **Implementation.** Run `implement-change`. All CSS must reference tokens from
   `web/src/tokens.css`; no hardcoded hex, rgba, rem spacing, px radius, or box-shadow values in
   new `.module.css` files. See `designs/design.md` for the token reference.
   Require: `Skill: implement-change - output below`.

6. **Post-implementation tests.** Run `test-change` to execute the component tests written in
   stage 3 and confirm all pass.
   Require: `Skill: test-change - output below`.

7. **Validation.** Run `validate-change`: type check, lint, component tests, and Playwright
   desktop screenshot of the implemented component in the running app to provide visual evidence.
   Require: `Skill: validate-change - output below`.

8. **Design review.** Run `design-reviewer` with the `.pen` screenshots and Playwright screenshot
   side-by-side. Reviewer compares spec intent vs implementation.
   Require: `Agent: design-reviewer - output below`.
   - Critical or High findings → fix implementation, re-validate (stage 7), re-run design-reviewer.
     Up to 3 loops. Record loop count and repeat artifact labels.
   - If Critical or High findings remain after 3 loops, stop with blockers.

9. **Code review.** Run `code-reviewer` when risk is medium, high, or system-level.
   Require: `Agent: code-reviewer - output below`.
   - Critical, High, or Major findings → fix, re-validate (stage 7), re-run `code-reviewer`.
     Up to 3 loops. Record loop count and repeat artifact labels.
   - If Critical, High, or Major findings remain after 3 loops, stop with blockers.

Stop on a blocked or failed step and return control to the manager. The manager owns
documentation maintenance and task-complete after this pipeline.

## Output Contract

Begin with `Pipeline: pen-to-code - output below` and report:
- status;
- `.pen` source file path;
- component file path(s) implemented;
- completed stage labels;
- test results summary;
- design-reviewer and code-reviewer verdicts with loop counts;
- blockers.
