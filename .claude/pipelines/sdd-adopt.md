# Pipeline: SDD Adopt

## Purpose

Pre-defined routing plan for introducing or expanding a Spec-Driven Development `docs/` tree
in a project that already has documentation, code, or both. It sequences the SDD bundle's
gap analysis, authoring skills, and review so existing material is reconciled rather than
discarded.

This pipeline is a routing artifact. It sequences existing capabilities. It does not
implement step logic and does not emit its own output artifact.

## When to Apply

- The project already has substantive documentation or code and the user wants to adopt or
  expand the SDD doc set.
- Use the bootstrap pipeline instead when starting from no docs.

## Inputs

- The repository root.
- The location(s) of any existing documentation, if known.
- Any tier preference or scope constraint from the user.

## Stages

| Stage | Capability | Required Visible Artifact |
| --- | --- | --- |
| 1. Intake | direct — confirm repo root, existing docs, scope | none |
| 2. Gap analysis | `Agent: sdd-gap-analyzer` | `Agent: sdd-gap-analyzer - output below` |
| 3. Confirm plan | direct — accept the plan; when it has ambiguous choices, confirm with the user | none |
| 4. Reconcile docs | `Skill: sdd-doc-author` (once per doc marked migrate/create) | `Skill: sdd-doc-author - output below` |
| 5. Features | `Skill: sdd-feature-author` (once per extracted feature) | `Skill: sdd-feature-author - output below` |
| 6. Index | `Skill: sdd-index-sync` | `Skill: sdd-index-sync - output below` |
| 7. Review | `Agent: sdd-spec-reviewer` | `Agent: sdd-spec-reviewer - output below` |
| 8. Suggest companions | direct — present this bundle's `RECOMMENDS.md` companions; install any the user adopts via the kit-adopt path | a note of companions offered and which were adopted |

Author docs in the order the gap-analysis plan specifies (foundational docs first). Stage 8
is opt-in and may be declined. Do not advance past a stage whose expected visible artifact is
missing.

## Authority Sources

- the `sdd-doc-set` convention
- the bundle's templates under `templates/`
- the stage 2 gap-analysis output

## Stop Conditions

- The gap analysis reports a fundamental conflict requiring a user decision — resolve at
  stage 3 before authoring.
- A doc-authoring or feature step blocks — resolve before advancing.
- `sdd-spec-reviewer` verdict is `Needs revision` — fix the cited findings, re-run the
  affected stage and stage 6, then re-run stage 7.
- The convention or repository root cannot be read — stop and report the missing source.

## Output Contract

The pipeline emits no artifact of its own. Each stage emits its own contract artifact as
listed above.
