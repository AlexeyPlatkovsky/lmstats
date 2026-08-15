# Instruction Change Pipeline

## Trigger

Use for explicitly approved creation or material change of TaskPilot runtime instruction artifacts.
Do not use it to run framework stages under `.manifesto/`.

## Ordered Steps

1. Run `maintain-instruction-system`. Require
   `Skill: maintain-instruction-system - output below`.
2. Run `instruction-evaluator` in isolated context. Require
   `Agent: instruction-evaluator - output below`.
3. Run `artifact-acceptance-tester` in isolated context with exactly nine scenarios per materially
   changed target. Require `Agent: artifact-acceptance-tester - output below`.
4. Run `validate-change` against references, frontmatter, layer boundaries, stale paths, and the
   final diff. Require `Skill: validate-change - output below`.

Stop on a blocked, failed, `Needs revision`, or `Reject / split required` result and return control
to the manager. If the target diff, change description, canonical template, or directly coupled
context is missing, report the pipeline blocked before acceptance. The manager owns task-complete.

## Output Contract

Begin with `Pipeline: instruction-change - output below` and report status, changed targets,
artifact labels, acceptance coverage, deviations, and blockers.
