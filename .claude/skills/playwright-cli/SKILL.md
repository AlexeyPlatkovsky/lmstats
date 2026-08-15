---
name: playwright-cli
description: Automates browser interactions for live UI exploration, testing, form filling, screenshots, and data extraction. Use when direct browser interaction is needed to answer questions that repository files cannot.
---

## Scope

- Drive live browser automation when repository files, docs, and tests cannot reliably answer the current question.
- Prefer repository evidence first. Run browser commands only when the codebase does not have the answer.
- On first use in a project, create `.playwright/cli.config.json` if it does not exist (this file is intentionally committed as project configuration, not gitignored).

## What Is Playwright CLI

[`playwright-cli`](https://playwright.dev/agent-cli/introduction) is a command-line tool for browser automation built on [Playwright](https://playwright.dev) (Microsoft's browser testing framework). It is invoked as a bash command and controls real browsers (Chrome, Firefox, WebKit, Edge) to navigate pages, interact with elements, capture screenshots, and inspect live UI state.

## Prerequisites

Before using `playwright-cli`, confirm:
- Node.js 20 or newer is available.
- `playwright-cli` is installed and available globally or through `npx`; see the official installation guide at <https://playwright.dev/agent-cli/installation>.
- `playwright-cli --help` or `npx playwright-cli --help` succeeds.
- Required browsers are available, or can be installed with `playwright-cli install-browser`.

A typical setup:
```bash
npm install -g @playwright/cli@latest
playwright-cli --help
playwright-cli install-browser
```

If the command is not available, stop and ask the user to set it up before continuing.

## TaskPilot Local Environment

TaskPilot has two local servers that must both be running for full UI testing:

| Service | URL | Start command |
| --- | --- | --- |
| Web UI (React/Vite dev) | `http://localhost:3000` | `cd web && npm run dev` |
| REST API (FastAPI/uvicorn) | `http://127.0.0.1:7152` | `uv run taskpilot serve` |
| OpenAPI docs | `http://127.0.0.1:7152/docs` | (starts with REST API) |

The Vite dev server proxies all `/api/*` requests to the REST API (`web/vite.config.ts`). If only the API needs testing without the UI, target `http://127.0.0.1:7152` directly. Canonical task data lives in `.taskpilot/` as YAML items and Markdown comments — browser automation must not modify these files directly.

If a required service is not reachable when the skill is invoked, stop immediately and ask the user to start it before continuing.

## Safety Constraints

- Do not modify source files or `.taskpilot/` canonical data files (YAML items, Markdown comments) via browser automation.
- Do not store credentials in session files or artifacts.
- Do not run full test suites — use targeted, minimal interactions.
- Do not perform destructive actions on live environments.
- Before any persistent, external, authenticated, or non-local state-changing interaction, confirm the target URL/environment is intended and the action is necessary for the user's request.
- Do not submit purchases, delete data, send messages, change permissions, or mutate live production data unless the user explicitly approved that exact action.
- Do not use authentication, persistent profiles, saved sessions, or stored credentials unless explicitly approved.
- TaskPilot is local-first and offline: never attempt to reach cloud endpoints or external services during browser automation unless the user explicitly requests it.

## Core Capabilities

- Navigate to URLs
- Click, double-click, type, fill forms, hover, drag, check/uncheck elements
- Take screenshots and capture accessibility snapshots
- Evaluate JavaScript expressions
- Inspect element attributes and DOM state
- Read console logs and network requests
- Manage named sessions, multiple tabs, and persistent browser profiles
- Mock and route network requests
- Record traces and videos for debugging
- Support multiple browser types: Chrome, Firefox, WebKit, Edge

## Procedure

1. Use the smallest targeted browser flow that can answer the question.
2. Avoid long command chains without observing state between steps.
3. Use refs from the latest accessibility snapshot for interactions whenever possible.
4. Re-snapshot after navigation, submissions, or major UI state changes because refs are only valid for the current snapshot.
5. Use selectors or locators only when refs are unavailable or insufficient, and state that choice in the evidence.
6. Capture the final page state with a snapshot or screenshot before reporting.

## Error Handling

When a browser command fails (page not found, element not found, timeout, JS error):
- If the failure may be caused by stale refs after navigation or page change, take one fresh snapshot and retry once only for non-destructive actions (navigate, snapshot, screenshot, read-only JavaScript evaluation, hover, scroll).
- Do not retry destructive, submitting, purchasing, deleting, or permission-changing actions without explicit user approval.
- Record unresolved failures as `UNKNOWN` with the command, error reason, and available evidence.
- Continue with any remaining independent actions.

## Artifact Organization

All output artifacts (screenshots, snapshots, traces, videos, PDFs) land under `.playwright/` via `outputDir` config. Screenshots can be placed in `.playwright/screenshots/` by using `--filename=screenshots/name.png`. This directory is gitignored by the project.

**Config file.** `.playwright/cli.config.json` must contain:

```json
{
  "outputDir": ".playwright"
}
```

**Alternative — environment variable (CLI/bash invocation only).** Set `PLAYWRIGHT_MCP_OUTPUT_DIR=.playwright` before invoking `playwright-cli`. Note: this env variable is only recognized by the `playwright-cli` bash command; it has no effect when `playwright-cli` runs as an MCP server.

The tool writes to `.playwright/` when neither config nor env variable is present. Always use one of the two methods above so artifacts land in the project-standard location.

When an artifact is part of the final evidence, use an explicit `--filename` when the command supports it.

## Verification

Before reporting completion, verify:
- The final page state was captured with a snapshot or screenshot.
- Claims about visual layout, canvas, charts, or non-accessible UI are supported by screenshots.
- Claims about text, controls, and forms are supported by accessibility snapshot evidence when available.
- Any console or network finding names the command used and the observed result.
- All live UI findings are marked `CONFIRMED_FROM_LIVE_UI`; unavailable evidence is marked `UNKNOWN`.

## Output Contract

Emit:

`Skill: playwright-cli - output below`

Then include:

| Field | Content |
| --- | --- |
| Status | `completed`, `skipped`, or `blocked` |
| URL / Environment | Page or app visited, including local/remote context when known |
| Session / Profile | Session name, profile mode, or `default in-memory` |
| Actions | Targeted steps performed |
| Findings | Each finding labeled `CONFIRMED_FROM_LIVE_UI` or `UNKNOWN` |
| Evidence | Snapshot excerpts, accessible names, stable refs/attributes, console/network facts, or artifact paths |
| Artifacts | Screenshot, snapshot, trace, video, or PDF paths, or `none` |
| Errors / Unknowns | Failed commands, missing access, unavailable credentials, or `none` |
