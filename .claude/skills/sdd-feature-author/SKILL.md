---
name: sdd-feature-author
description: Scaffolds or updates one feature folder (requirements, tasks, scenarios) as a unit in a docs/ SDD tree, with stable feature, requirement, task, and scenario IDs and traceability links. Use when adding or revising a feature.
---

## Scope

- Create or revise exactly one feature folder per run at `features/F<NNN>_<short-name>/`,
  producing or updating `requirements.md`, `tasks.md`, and `scenarios.md` together.
- Assign and preserve IDs per the doc-set convention: feature `F<NNN>`, requirement
  `F<NNN>-R<n>`, task `F<NNN>-T<n>`, scenario `F<NNN>-S<n>`.
- Maintain traceability: each requirement links up to an `idea.md` scope item or
  `roadmap.md` entry, and down to at least one task and one scenario.
- Do not edit main or extension docs, rebuild `INDEX.md`, or renumber existing IDs.

## Required Environment

This skill ships in the SDD bundle and depends on files that travel with it:
- the `sdd-doc-set` convention (feature-folder schema, ID scheme, traceability spine);
- `.claude/conventions/documentation-quality.md` for gap disclosure, evidence boundaries, and
  assumptions in project documents;
- the feature templates under the bundle's `templates/features/F000_template/`.

If any required file is unavailable, report it as a blocker before writing.

## Inputs

- Feature intent and short name.
- The `idea.md` scope item or `roadmap.md` entry the feature serves.
- Mode: `new` or `revise` (with the existing feature ID when revising).

## Procedure

Apply the Stop Conditions throughout; halt and report when any is met.

1. Determine the feature ID: in `new` mode use the next free sequential `F<NNN>`; in
   `revise` mode use the existing folder. Build the slug `F<NNN>_<short-name>`.
2. Write `requirements.md`: summary, the served `idea`/`roadmap` link, requirements with
   `F<NNN>-R<n>` IDs, acceptance criteria, constraints, and explicit out-of-scope.
3. Write `tasks.md`: tasks with `F<NNN>-T<n>` IDs, each linked to the requirement(s) it
   implements, with status and dependencies.
4. Write `scenarios.md`: Gherkin scenarios with `F<NNN>-S<n>` IDs linked to requirements,
   plus a manual verification checklist.
5. Verify each requirement has at least one task and one scenario. Flag any requirement,
   task, or scenario that lacks a link as a traceability gap.
6. Note that `INDEX.md` needs re-syncing. Do not edit `INDEX.md` here.

## Stop Conditions

Stop and report a blocker when:
- a requirement cannot be traced up to an `idea.md` or `roadmap.md` item;
- two stated requirements directly conflict;
- the chosen feature ID or slug collides with an existing feature.

## Output Contract

Emit:

`Skill: sdd-feature-author - output below`

Then include:

| Field | Content |
| --- | --- |
| Status | `completed`, `blocked`, or `skipped` |
| Feature | `F<NNN>_<short-name>` |
| Mode | `new` or `revise` |
| Requirements | Count and IDs |
| Tasks | Count and IDs |
| Scenarios | Count and IDs |
| Traceability gaps | Requirements without a task or scenario, or `none` |
| INDEX sync needed | `yes` |
| Blockers | Unresolved issues, or `none` |
