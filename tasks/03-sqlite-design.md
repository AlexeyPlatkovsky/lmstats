# Task 03 — SQLite Persistence Design

You are working on the existing **LM Stats Viewer** repository.

This is **stage 3 of 8** for v0.2.

Do not implement persistence yet.

## Goal

Design the smallest correct SQLite persistence layer required for v0.2.

## Inputs

Read:

```text
AGENT.md
docs/v0.2/02-baseline.md
```

Inspect the current code only as needed.

## v0.2 persistence requirements

Every valid completed LM Studio prediction must eventually be stored.

The application will use Python's built-in:

```python
sqlite3
```

No ORM.

No migration framework.

History must survive viewer restart.

The current/latest prediction should be loadable from SQLite on startup.

## Required design

Create:

```text
docs/v0.2/03-sqlite-design.md
```

Define:

### 1. Database location

Choose one predictable local path and explain it.

Avoid writing test data into the production DB.

### 2. Schema

Design a single simple `predictions` table.

It should support at least:

```text
id
timestamp
model
tokens_per_second
time_to_first_token_seconds
total_time_seconds
prompt_tokens
output_tokens
total_tokens
stop_reason
response
raw_event
```

Define SQLite types and nullability.

Do not add cache fields yet.

Do not add internal-request classification yet.

### 3. Timestamp policy

Define one unambiguous storage format.

Prefer normalized UTC internally.

Explain how local browser time will eventually be derived.

### 4. Indexes

Define only indexes needed for:

- latest prediction
- time-range queries
- per-model time-range queries

### 5. Connection strategy

Choose a simple safe pattern for FastAPI reads + collector writes.

Avoid unsafe shared-connection assumptions.

Prefer correctness and simplicity.

### 6. Persistence flow

Specify:

```text
LM Studio event
→ parse
→ normalize
→ SQLite insert
→ update latest state
→ SSE notification
```

Persistence must not depend on an attached browser.

### 7. Startup behavior

Specify:

- initialize schema idempotently
- preserve existing DB
- load latest stored prediction
- then start live collection

### 8. Test cases

List concrete tests for:

- new DB
- schema idempotence
- insert
- latest lookup
- persistence across reopen
- null optional fields
- time boundaries
- test DB isolation

## Constraints

Do not design:

- migrations
- cache correlation
- response search
- analytics tables
- aggregation tables
- retention policies
- user settings

## Required verification

No product implementation is required, but run current:

```text
lint
tests
coverage
```

to confirm the repository remains healthy.

## Deliverable

`docs/v0.2/03-sqlite-design.md`

The document must be detailed enough that a fresh agent can implement persistence without needing the previous conversation.

## Stop condition

Stop after the SQLite design is complete.
