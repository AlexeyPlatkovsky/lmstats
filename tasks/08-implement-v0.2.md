# Task 08 — Implement and Release LM Stats Viewer v0.2

You are working on the existing **LM Stats Viewer v0.1** repository.

This is **stage 8 of 8**.

This is the implementation stage.

Do not redesign the feature. The architecture, schema, API, UI behavior, tests, and release gates were prepared in the previous stages.

## Mandatory inputs

Before changing code, read:

```text
AGENT.md
docs/v0.2/02-baseline.md
docs/v0.2/03-sqlite-design.md
docs/v0.2/04-history-api-design.md
docs/v0.2/05-graph-ui-design.md
docs/v0.2/06-test-plan.md
docs/v0.2/07-implementation-plan.md
```

Follow them.

If a design document conflicts with the actual working repository, make the smallest safe adjustment and document it. Do not perform a new architecture exercise.

## Goal

Release **LM Stats Viewer v0.2** with:

1. existing v0.1 latest-generation view preserved
2. SQLite persistence
3. latest stored generation restored after viewer restart
4. generation-speed history graph
5. ranges:
   - 5m
   - 1h — default
   - 24h
6. dynamic bucketing
7. separate model series
8. 95%+ Python coverage
9. lint/tests/review/browser release gates passing

## Work test-first

Follow the implementation order in:

```text
docs/v0.2/07-implementation-plan.md
```

Use TDD where practical.

After every meaningful unit of work, run the focused checks rather than waiting until the end.

## Product scope

### SQLite

Use Python built-in:

```python
sqlite3
```

No ORM.

Persist every valid completed prediction according to the approved schema.

Database must survive application restart.

Use temporary DBs in tests.

### Current view

Preserve the existing v0.1 hero/latest display.

Generation speed remains the most visually prominent value.

On startup, if persisted telemetry exists, load the latest stored prediction immediately.

### History API

Implement only the approved history endpoint/ranges:

```text
5m
1h
24h
```

Validate ranges.

Keep model series separate.

Aggregate from raw SQLite rows according to the approved bucketing rules.

Do not persist bucket results.

### Graph UI

Add one simple historical generation-speed graph below the current metrics.

Controls:

```text
[ 5m ] [ 1h ] [ 24h ]
```

Default:

```text
1h
```

Use plain HTML/CSS/JavaScript with SVG or Canvas.

No frontend framework.

Refresh the selected history after a live generation event.

## Explicitly out of scope

Do NOT add:

- custom dates
- summary statistics table
- median/min/max analytics
- cache ratio
- internal request classification
- prompt-size graph
- response history browser
- CSV export
- settings
- migrations
- authentication
- React/Vue/etc.
- unrelated refactoring

## Automated verification

Run throughout development:

```text
ruff
pytest
pytest-cov
```

Final Python application coverage must be:

```text
>= 95%
```

The configured coverage gate must fail below 95%.

Do not manipulate coverage exclusions to pass artificially.

## Real LM Studio verification

After automated checks pass, run the actual application.

The collector must continue using:

```bash
lms log stream --source model --filter output --stats --json
```

The model executing this task is itself running through LM Studio, so your own generation can appear as real telemetry.

Do NOT:

- restart LM Studio
- kill LM Studio
- unload its model
- modify LM Studio server configuration

Verify at least one real generation is:

```text
parsed
→ persisted to SQLite
→ shown as latest
→ returned by history API
→ represented in the graph
```

## Restart persistence verification

Verify explicitly:

1. store a real generation
2. confirm DB row exists
3. stop only LM Stats Viewer
4. restart LM Stats Viewer
5. confirm latest telemetry is restored
6. confirm historical graph data is still available

Do not delete/recreate the DB during this test.

## Playwright verification

Use installed:

```text
playwright-cli
```

Verify in a real browser:

1. page loads
2. current speed remains visually dominant
3. current model/stats render
4. graph renders
5. 1h is selected by default
6. 5m works
7. 1h works
8. 24h works
9. range switching does not reload the page
10. multiple model series are not merged
11. empty period is handled
12. live generation refreshes graph
13. persisted latest data survives viewer restart
14. no significant browser console errors
15. layout remains readable

Use screenshots if useful.

Fix real issues found.

## Code review

After implementation, tests, real integration, and Playwright verification:

Run the repository's:

```text
code-reviewer
```

subagent defined in:

```text
.claude/agents/code-reviewer.md
```

Review its findings.

Fix valid CRITICAL/HIGH/MEDIUM issues and meaningful LOW issues when inexpensive.

Do not blindly implement incorrect suggestions.

After fixes, rerun affected tests and then the full release gate.

## Final release gate

Do not claim completion until:

```text
lint: PASS
tests: PASS
coverage >=95%: PASS
real LM Studio telemetry: PASS
SQLite persistence: PASS
restart persistence: PASS
5m history: PASS
1h history: PASS
24h history: PASS
1h default: PASS
multiple models separate: PASS
playwright-cli: PASS
code-reviewer executed: PASS
review findings addressed: PASS
README updated: PASS
```

## README

Update the existing README concisely with:

- SQLite persistence
- DB location
- 5m / 1h / 24h graph
- default 1h
- lint command
- test command
- coverage command
- 95% requirement

Do not write a long README.

## Final response

Only after the release gate passes, respond concisely:

```text
Implemented:
- ...

Verification:
- lint: PASS
- tests: X passed
- coverage: XX.XX%
- real LM Studio telemetry: PASS
- SQLite persistence/restart: PASS
- 5m/1h/24h history: PASS
- playwright-cli: PASS
- code-reviewer: PASS

Database:
- <path>

Run:
- <command>

Open:
- <URL>

Known limitations:
- ...
```

Do not provide a long narrative.
