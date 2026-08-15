# Task 06 — v0.2 Test Plan and Fixtures

You are working on the existing **LM Speed Viewer** repository.

This is **stage 6 of 8** for v0.2.

Do not implement the v0.2 feature yet.

## Goal

Prepare a concrete TDD test plan so the implementation stage can work test-first and remain bounded.

## Inputs

Read:

```text
AGENT.md
docs/v0.2/02-baseline.md
docs/v0.2/03-sqlite-design.md
docs/v0.2/04-history-api-design.md
docs/v0.2/05-graph-ui-design.md
```

## Required work

Create:

```text
docs/v0.2/06-test-plan.md
```

The plan must define the exact tests to add during implementation.

## Required test groups

### A. Existing parser regression

Preserve:

- valid prediction
- malformed JSON ignored
- unrelated event ignored
- missing optional fields tolerated

### B. SQLite

Specify tests for:

- DB initialization
- repeated initialization
- insertion
- latest prediction
- reopening persistent DB
- null optional values
- production/test DB isolation
- timestamp boundary correctness

### C. History queries

Specify tests for:

```text
5m
1h
24h
```

Include:

- rows just inside boundary
- rows just outside boundary
- multiple models
- missing speed
- bucket average
- request count
- empty DB
- deterministic ordering

### D. API

Specify endpoint tests for:

- default range
- 5m
- 1h
- 24h
- invalid range
- empty history
- multiple model response

### E. Startup behavior

Specify test for:

- existing DB contains prediction
- application starts
- latest stored prediction becomes current state before a new live event

### F. Collector write path

Specify test that:

```text
valid event
→ database row
→ latest state update
→ browser notification path
```

Avoid requiring real LM Studio for this unit/integration test.

### G. Real integration acceptance test

Define manual/automated acceptance:

- run app
- allow a real LM Studio generation
- verify SQLite row
- verify latest UI
- verify history API
- restart viewer only
- verify persisted data remains

### H. Playwright acceptance

Define browser checks from the UI design.

## Coverage

The full Python application must remain:

```text
>= 95%
```

Identify likely hard-to-cover branches and how to test them legitimately.

Do not use broad coverage exclusions.

## Test fixture strategy

Define reusable fixtures for:

- temporary SQLite path
- fixed UTC clock/time reference where needed
- sample normalized prediction
- sample LM Studio raw JSON event
- FastAPI test client

Avoid flaky tests based on real current time where deterministic timestamps can be injected.

## Required verification

Run current:

```text
lint
tests
coverage
```

## Deliverable

`docs/v0.2/06-test-plan.md`

## Stop condition

Stop after the implementation-stage test plan is complete.
