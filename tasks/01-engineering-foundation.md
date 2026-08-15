# Task 01 — Engineering Foundation and Release Gates

You are working on the existing **LM Speed Viewer v0.1** repository.

This is **stage 1 of 8** for v0.2.

Do not implement SQLite history or the graph in this stage.

## Goal

Create the engineering rules and quality gates that every later stage must follow.

## Required work

### 1. Inspect the repository

Before changing anything:

- inspect the current project structure
- identify the Python application modules
- identify existing tests
- identify the current launch command
- run the existing test suite
- do not rewrite working v0.1 code

### 2. Add linting

Use **Ruff** unless the project already has a suitable linter.

Configure a simple command such as:

```bash
ruff check .
```

Keep configuration practical. Do not enable a huge unrelated rule set.

### 3. Add coverage

Use:

- `pytest`
- `pytest-cov`

Create a coverage command that fails if Python application coverage is below **95%**.

Example concept:

```bash
pytest --cov=<app-module> --cov-report=term-missing --cov-fail-under=95
```

Measure meaningful application Python code only.

Do not artificially inflate coverage.

### 4. Create `AGENT.md`

Create repository-root:

```text
AGENT.md
```

Keep it concise.

It must instruct future agents to:

- use TDD where practical
- add a failing regression test before fixing bugs where practical
- run relevant tests after every significant piece of work
- run lint regularly
- run full tests + coverage before completion
- use `playwright-cli` to verify meaningful UI changes
- run the `code-reviewer` subagent after implementation is complete
- fix valid review findings and rerun affected checks
- avoid unrelated scope expansion

### 5. Create code-reviewer subagent

Create:

```text
.claude/agents/code-reviewer.md
```

Use the valid Claude Code subagent format available in the environment.

The reviewer should inspect completed changes for:

- correctness
- regressions
- unnecessary complexity
- error handling
- SQLite correctness
- concurrency issues
- FastAPI/SSE issues
- test quality
- maintainability
- compliance with AGENT.md
- scope creep

Prioritize findings:

```text
CRITICAL
HIGH
MEDIUM
LOW
```

It should review and report, not rewrite the application automatically.

### 6. Define release gates

Create a small documented set of final release checks, either inside `AGENT.md` or an existing appropriate project document.

The release gate must require:

```text
lint: PASS
tests: PASS
coverage >= 95%: PASS
playwright-cli verification: PASS for UI changes
code-reviewer: PASS / findings addressed
```

Do not add a heavyweight CI system unless one already exists and can be extended trivially.

## Required verification

Run:

- lint
- tests
- coverage

Fix issues caused by this stage.

If the existing application cannot yet reach 95% without substantial product changes, add meaningful tests around current v0.1 behavior. Do not implement v0.2 product functionality early.

## Deliverable

Finish with a concise summary containing:

- files created/changed
- lint command
- test command
- coverage command
- actual coverage
- current test count
- any limitations

## Stop condition

Stop after the engineering foundation is established and verified.

Do **not** start SQLite or graph implementation.
