# Task 04 — History Query and Aggregation Design

You are working on the existing **LM Speed Viewer** repository.

This is **stage 4 of 8** for v0.2.

Do not implement the history API yet.

## Goal

Design the backend contract for the v0.2 historical speed graph.

## Inputs

Read:

```text
AGENT.md
docs/v0.2/02-baseline.md
docs/v0.2/03-sqlite-design.md
```

## Required product behavior

The UI will offer:

```text
5m
1h
24h
```

Default:

```text
1h
```

The graph displays generation speed over time.

Multiple models must remain separate.

Raw prediction data is stored individually.

Longer periods should be dynamically bucketed.

## Required design

Create:

```text
docs/v0.2/04-history-api-design.md
```

Define:

### 1. API endpoint

Prefer a simple contract such as:

```text
GET /api/history?range=5m
GET /api/history?range=1h
GET /api/history?range=24h
```

Specify:

- allowed range values
- default behavior
- invalid-range behavior
- response structure

### 2. Time windows

Define exact semantics:

```text
5m = now minus 5 minutes through now
1h = now minus 1 hour through now
24h = now minus 24 hours through now
```

Use UTC internally.

### 3. Bucketing

Use the agreed approach:

```text
5m  → raw predictions or very fine buckets
1h  → approximately 1-minute buckets
24h → approximately 15-minute buckets
```

Choose exact deterministic rules.

### 4. Aggregation

For each model and bucket calculate:

```text
average tokens/sec
request count
```

Do not mix models.

Do not store aggregated rows in SQLite.

### 5. Empty data

Define a stable API response for no data.

### 6. Ordering

Define deterministic ordering for:

- model series
- points within a series

### 7. SQL/query strategy

Describe how queries should use the timestamp/model indexes.

Avoid loading the entire DB for a short range.

### 8. Test matrix

Define tests for:

- 5m
- 1h
- 24h
- invalid range
- exact time boundaries
- old rows excluded
- multiple models separated
- bucket averages correct
- empty DB
- rows with missing speed

Specify whether rows with `tokens_per_second = NULL` should be excluded from speed aggregation.

## Constraints

Do not add:

- custom date range
- summary table
- median/min/max
- cache analytics
- prompt-size graph
- export

## Required verification

Run current quality gates:

```text
lint
tests
coverage >= 95%
```

## Deliverable

`docs/v0.2/04-history-api-design.md`

## Stop condition

Stop after the backend history contract is fully specified.
