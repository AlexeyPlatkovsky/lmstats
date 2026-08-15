# Task 07 — Implementation Plan and Release Checklist

You are working on the existing **LM Speed Viewer** repository.

This is **stage 7 of 8** for v0.2.

Do not implement v0.2 yet.

## Goal

Convert all approved design documents into one precise, bounded implementation plan for the final stage.

## Inputs

Read all:

```text
AGENT.md
docs/v0.2/02-baseline.md
docs/v0.2/03-sqlite-design.md
docs/v0.2/04-history-api-design.md
docs/v0.2/05-graph-ui-design.md
docs/v0.2/06-test-plan.md
```

Inspect the current repository as needed.

## Required work

Create:

```text
docs/v0.2/07-implementation-plan.md
```

The plan must be specific enough that the final implementation agent does not need to redesign the feature.

## Required sections

### 1. Files to create/change

List expected files and purpose.

Prefer small changes.

Avoid speculative modules.

### 2. Exact implementation order

Use TDD.

A preferred sequence is:

```text
1. add DB tests
2. implement SQLite layer
3. run focused tests + lint
4. add history-query tests
5. implement history queries
6. run focused tests + coverage
7. add API tests
8. implement API
9. run API tests + lint
10. add startup/latest persistence test
11. implement startup behavior
12. run regression suite
13. implement graph UI
14. run full automated checks
15. run real LM Studio integration
16. run playwright-cli
17. run code-reviewer
18. fix valid findings
19. rerun all release gates
```

### 3. Scope boundaries

Explicitly prohibit:

- custom date picker
- summary statistics table
- cache ratio
- internal request filtering
- extra analytics
- frontend framework
- migrations
- export
- settings
- broad refactors

### 4. Risk list

Identify likely risks:

- timestamp handling
- SQLite concurrency
- duplicate inserts
- multiple models mixed together
- long-range graph point count
- SSE refresh behavior
- regression of hero/current view

For each risk define the corresponding test/gate.

### 5. Release checklist

Create a final checklist requiring:

```text
Ruff: PASS
pytest: PASS
coverage >=95%: PASS
real LM Studio event persisted: PASS
restart persistence: PASS
history 5m/1h/24h: PASS
default 1h: PASS
multiple models separated: PASS
playwright-cli: PASS
code-reviewer executed: PASS
review findings addressed: PASS
final regression checks: PASS
README updated: PASS
```

### 6. Final-stage token discipline

The final implementation agent must not spend time redesigning.

It should:

- trust these documents unless code reality proves them wrong
- implement only specified scope
- run focused checks incrementally
- stop investigating unrelated issues
- use concise tool outputs where possible

## Required verification

Run current repository quality gates:

```text
lint
tests
coverage
```

## Deliverable

`docs/v0.2/07-implementation-plan.md`

## Stop condition

Stop after the plan and release checklist are complete.

Do not start implementation.
