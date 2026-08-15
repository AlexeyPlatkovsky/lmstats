# Task 02 — v0.1 Baseline Audit and Current Architecture Map

You are working on the existing **LM Speed Viewer** repository.

This is **stage 2 of 8** for v0.2.

Stage 1 should already have created the engineering quality foundation.

Do not implement v0.2 product features in this stage.

## Goal

Create an accurate technical baseline of the working v0.1 application so later stages can make small, controlled changes.

## Required work

### 1. Read project instructions

Read:

```text
AGENT.md
```

Follow it.

### 2. Inspect current implementation

Determine:

- application entry point
- LM Studio log subprocess lifecycle
- JSON parsing path
- normalized prediction representation
- current in-memory latest-prediction state
- SSE implementation
- frontend update flow
- existing tests
- current error handling
- shutdown behavior

### 3. Verify the current system

Run:

- lint
- tests
- coverage

Start the application if needed.

Use the real LM Studio environment only where safe.

Do not restart or kill LM Studio.

### 4. Create architecture note

Create:

```text
docs/v0.2/02-baseline.md
```

Keep it concise.

Document:

- current project structure
- data flow from `lms log stream` to browser
- current prediction fields
- important functions/modules and their responsibility
- existing tests and gaps
- likely extension points for persistence/history
- risks that later stages must preserve

### 5. Record baseline behavior

Include the expected current UI behavior:

- latest generation only
- speed remains primary metric
- model
- TTFT
- prompt/output/total tokens
- generation time
- collector status
- automatic live update

These are regression requirements for v0.2.

## Do not

- add SQLite
- add history API
- add graph UI
- redesign the frontend
- perform broad refactoring
- create speculative abstractions

Only make tiny fixes if required to restore the existing baseline.

## Required verification

Before finishing:

```text
lint: PASS
tests: PASS
coverage >= 95%: PASS
```

## Deliverable

Create `docs/v0.2/02-baseline.md`.

In the final response report:

- baseline status
- tests
- coverage
- key extension points
- any blockers discovered

## Stop condition

Stop after the baseline is accurately documented and verified.
