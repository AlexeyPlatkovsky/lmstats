---
name: implement-change
description: Implements production behavior from an accepted TaskPilot specification or explicit low-risk request. Does not own independent review or final closure.
---

# Implement Change

Prerequisites: an accepted specification or explicit behavior, known success criteria, and a
planned validation route.

1. If the request is purely a task-tracking operation with no implementation scope, do not proceed
   with this skill. Redirect a read-only query or a technical-field-only update (status, priority,
   timestamps, links) to `.claude/skills/track-with-taskpilot/SKILL.md` directly. Return item
   creation, a title/description change, or a comment-body write to the manager for
   `.claude/pipelines/backlog-change.md`, which owns the grounding step that skill's write gate
   requires.
2. If the manager's output or the user's instruction identifies a TaskPilot item ID for this work
   (task-backed), load `.claude/skills/track-with-taskpilot/SKILL.md` and read the item state to
   confirm it exists, capture current status, and prepare for status transitions
   (e.g. backlog → in_progress). If the skill cannot be loaded or the item does not exist, report
   a blocker and stop.
3. Read affected code, tests, conventions, and decisions.
   For WebUI component-library or existing-page UI work, include
   `.claude/conventions/ui-component-library.md`.
4. Verify the implementation scope still matches accepted specs, roadmap, design docs, and recorded
   open questions. If implementation would expand or narrow release scope, change an accepted
   editable/read-only field boundary, alter persistence or API contracts, or resolve an open product
   question without explicit approval, stop and report a scope-delta blocker. Do not convert an
   ambiguous request into implemented behavior.
5. For every requirement in scope, enumerate boundary conditions:
   - null / empty / missing / unrecognized inputs (in PATCH semantics
     ``null`` = explicitly cleared field, ``missing`` = not sent — distinct);
   - conflicting or duplicate state (existing project, repeated id, etc.);
   - silent-failure paths (files that can't be parsed, unreadable, wrong format);
   - error-envelope overlap with framework defaults (same status code,
     different body shape from the framework's own error handler).

   Map each boundary to an observable assertion or to a documented limitation.
   Report the resulting table as part of the artifact. The boundary-condition
   table complements the test plan produced by ``test-change`` step 3 — it is
   not a replacement. When the pipeline deferred tests (mapping-only mode),
   this step must check that the existing mapping is complete and add any
   boundaries discovered during implementation.
6. Implement the smallest complete vertical slice.
7. Keep domain rules in services and translation in adapters.
8. Preserve canonical-file-first writes and deterministic outputs.
9. Add only production and directly required support changes; test implementation belongs to
   `test-change`.
10. Run narrow compile or static checks needed to catch implementation errors
    and code-quality issues — including unused parameters, unused imports,
    and dead code. Use the project's configured linter for the language
    (ruff for Python, ESLint for TypeScript). If no linter is configured,
    propose installing one; add it only with user approval, or document
    the gap as a blocker.
11. Inspect the implementation diff for unrelated churn, leaked abstractions, and missing errors.
12. If the work was task-backed, load `.claude/skills/track-with-taskpilot/SKILL.md` and update the
    item status (e.g. ``in_progress`` → ``done``) when implementation is complete. If the update
    fails, report the error and do not claim completion. Do not modify
    ``.taskpilot/items/*.yaml`` files directly — always use the track-with-taskpilot skill. A status
    transition needs no grounding artifact. Writing or rewriting a title, description, or comment body
    is out of scope for this skill: stop, report it, and return control to the manager for
    `.claude/pipelines/backlog-change.md`. Do not run `ground-request` from here.

Stop for an unapproved breaking contract, canonical migration, production dependency, destructive
operation, security model, or architecture choice.

The artifact begins with `Skill: implement-change - output below` and reports status,
scope-delta result, behavior, changed files, assumptions, narrow checks, deviations, and blockers.
