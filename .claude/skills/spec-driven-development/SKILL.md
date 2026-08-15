---
name: spec-driven-development
description: Creates or refines an implementation-ready TaskPilot specification before non-trivial behavior, contract, persistence, API, or cross-layer work. Does not implement production code.
---

# Specification-Driven Development

Read `references/spec-template.md`, `.claude/conventions/documentation-quality.md`, and the
relevant sections of `.claude/docs/README.md`.

1. Inspect the concept, related specs and decisions, affected code, and tests.
2. Before creating or updating a specification, identify whether the request changes accepted
   product scope, release scope, editable/read-only field boundaries, persistence behavior, API
   contracts, or an open question. If it does, emit a scope-delta summary and stop until the user
   explicitly approves the scope change. The summary must state current accepted behavior,
   requested or implied behavior, why it is a scope change, available options, and any
   recommendation. Do not amend a spec to make the new behavior appear accepted before that
   approval.
3. State the user outcome, current behavior, boundaries, and non-goals.
4. Convert requirements into observable behavior; mark unsupported inferences as assumptions.
5. Define only affected domain concepts, canonical files, services, CLI/API contracts, and UI
   states.
6. Write independently testable Given/When/Then acceptance criteria.
7. Select test levels using `.claude/skills/test-change/references/test-strategy.md`.
8. Identify migration, compatibility, data-loss, concurrency, and cross-platform risks.
9. Split implementation into small vertical slices with observable completion.
10. Create or update `docs/specs/<descriptive-slug>.md`.

Stop before choosing between materially different product contracts without user authority.

The artifact begins with `Skill: spec-driven-development - output below` and reports status,
scope-delta result, specification path, decisions, assumptions, acceptance criteria coverage,
slices, planned validation, and blockers.
