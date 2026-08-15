---
name: maintain-docs
description: Synchronizes TaskPilot specifications, decisions, guides, commands, APIs, architecture, and domain facts after a change affects them.
---

# Maintain Documentation

Read `.claude/conventions/reference-docs.md` and
`.claude/conventions/documentation-quality.md`.

1. Inspect the actual diff and completed behavior. When invoked with no diff to repair a
   documentation gap or defect reported by another capability, that report plus its cited source
   evidence is the input instead of a diff, and the source evidence is the fact to document.
2. Find authoritative documentation roots through `.claude/docs/README.md`.
3. Determine whether behavior, workflows, commands, setup, architecture, contracts, vocabulary, or
   known failure modes changed.
4. Compare any proposed documentation update against accepted specs, roadmap, design docs, and
   recorded open questions. Documentation may reflect approved behavior, or implemented behavior
   that does not conflict with accepted scope. If the doc update would expand or narrow release
   scope, change editable/read-only boundaries, alter persistence or API contracts, or resolve an
   open product question, stop and report a scope-delta blocker instead of normalizing the change.
5. Update only affected authoritative sections and their indexes or links.
6. Update specification status and acceptance evidence when implementation completed.
7. When all tasks for a feature are implemented and the feature has passed pipeline validation,
   archive the feature:
   a. Read `docs/features/F<NNN>_<short-name>/tasks.md` and confirm every task has a terminal
      status (implemented, completed, or equivalent). If `tasks.md` is missing or unparseable,
      skip archiving and report a blocker. Skip archiving if any task is not terminal.
   b. Move the feature folder from `docs/features/F<NNN>_<short-name>/` to
      `docs/features/archive/F<NNN>_<short-name>/`. Create the archive target directory if it does not exist.
   c. Run `sdd-index-sync` to refresh INDEX.md with the archive path.
   This step is evaluated during documentation maintenance after the implementing pipeline
   completes. It applies when the pipeline's change completes the last remaining task of a feature.
   The validation gate is already enforced by the pipeline's `validate-change` step before this
   skill runs; the tasks.md terminal-status check is the file-state gate.
8. Create an ADR only for a durable architecture decision with meaningful alternatives and
   consequences.
9. Verify commands, paths, examples, names, and links against repository facts.

Do not modify production code or tests. Report rather than guess when documentation should change
but the correct contract is unclear or outside scope.
If the diff, authoritative source, or implemented behavior cannot be inspected, stop and report the
missing context as blocked. A run invoked without a diff under step 1's reported-gap input mode is
not missing context; it is blocked only when that report cites no source evidence.

The artifact begins with `Skill: maintain-docs - output below` and reports status as documentation
updated, checked/no update needed, or blocked, plus scope-delta result, sources, files, conflicts,
assumptions, and blockers.
