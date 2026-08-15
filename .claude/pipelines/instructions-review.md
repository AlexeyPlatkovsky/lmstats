# Instructions Review Pipeline

## Trigger

Use for reviewing one or more existing TaskPilot instruction artifacts (skills, agents, pipelines,
conventions, root contracts, or any runtime instruction file) and iteratively fixing findings
through a bounded review-fix loop.

Do not use for framework-stage work under `.manifesto/`.

## Input

Supply one of:

- `named: <path>[,<path>...]` — comma-separated list of specific artifact paths to review.
- `all` — review every instruction artifact under `.claude/` and root `AGENTS.md`.

## Loop

Maximum 3 review-fix cycles. The loop counter starts at 0. If after the fix step the counter is
still below the maximum, return to the review step. On exhaustion, stop with blockers.

## Ordered Steps

1. Run `instruction-evaluator` in isolated context on the target artifacts.
   Require `Agent: instruction-evaluator - output below`.

2. Run `artifact-acceptance-tester` in isolated context with exactly nine scenarios per reviewed
   artifact. Require `Agent: artifact-acceptance-tester - output below`.

3. Evaluate results:
   - If the evaluator verdict is `Accept` or `Accept with minor edits` **and** the tester verdict
     does not require changes: proceed to step 5.
   - Otherwise (any `Needs revision`, `Reject / split required`, blocked status, or tester failure):
     proceed to step 4.

4. Run `maintain-instruction-system` to fix the findings. Require
   `Skill: maintain-instruction-system - output below`.
   Increment the loop counter.
   - If loop counter < 3: return to step 1.
   - If loop counter >= 3: stop with blockers (`Loop exhausted after 3 cycles`).

5. Run `validate-change` against references, frontmatter, layer boundaries, stale paths, and the
   final diff. Require `Skill: validate-change - output below`.

6. Run `task-complete`. Require `Skill: task-complete - output below`.

Stop on a blocked, failed, or loop-exhausted step and return control to the manager with the loop
counter and a summary of unresolved findings.

## Output Contract

Begin with `Pipeline: instructions-review - output below` and report status, target artifacts, loop
counter and attempts, completed handoffs, artifact labels, skipped steps with reasons, deviations,
and blockers.
