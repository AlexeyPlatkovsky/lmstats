# Task 05 — Minimal Historical Graph UI Specification

You are working on the existing **LM Stats Viewer** repository.

This is **stage 5 of 8** for v0.2.

Do not implement the UI yet.

## Goal

Define a minimal UI extension that preserves the working v0.1 page and adds one historical generation-speed graph.

## Inputs

Read:

```text
AGENT.md
docs/v0.2/02-baseline.md
docs/v0.2/04-history-api-design.md
```

Inspect the current `index.html` / CSS / JS.

## Product constraints

The existing latest-speed view remains primary.

Generation speed must still visually dominate the page.

Below the current metrics, add only:

```text
Generation Speed History

[ 5m ] [ 1h ] [ 24h ]

<graph>
```

Default selected range:

```text
1h
```

## Required design

Create:

```text
docs/v0.2/05-graph-ui-design.md
```

Define:

### 1. Placement

Specify where the new graph sits relative to the current v0.1 hero speed and metrics.

Do not redesign the page.

### 2. Range selector

Define:

- buttons
- active state
- default 1h
- no page reload
- behavior during API request
- behavior on failure

### 3. Graph

Use plain browser technology.

Prefer:

```text
SVG
```

or Canvas if clearly simpler.

Do not introduce a frontend framework.

Define:

```text
X axis = time
Y axis = tokens/sec
one series per model
```

### 4. Colors

Define a small deterministic series palette that works on the current dark theme.

Do not rely on only one green for all models.

### 5. Legend

Keep it compact.

### 6. Empty state

Example:

```text
No generations recorded in this period.
```

### 7. Live update behavior

When the existing SSE announces a new prediction:

- latest-generation metrics continue updating
- currently selected history range should refresh
- avoid excessive refresh loops

### 8. Basic tooltip

If simple, specify a lightweight hover tooltip with:

```text
time
model
average tokens/sec
request count if bucketed
```

Tooltip is optional if it would materially complicate v0.2.

### 9. Browser verification checklist

Define what Playwright must verify:

- current hero still visible
- 1h selected by default
- 5m / 1h / 24h switches work
- graph renders
- empty state works
- multiple series remain distinguishable
- live event refreshes graph
- no major console errors

## Constraints

Do not design:

- custom dates
- table of statistics
- extra KPI cards
- zoom/pan
- graph export
- response history
- settings

## Required verification

Run current:

```text
lint
tests
coverage
```

No product UI change should be made in this stage.

## Deliverable

`docs/v0.2/05-graph-ui-design.md`

## Stop condition

Stop after the UI behavior is clearly specified.
