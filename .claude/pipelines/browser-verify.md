---
name: browser-verify
description: Live browser investigation, WebUI verification, and business-logic confirmation through the running app without code changes.
---

# Browser Verify Pipeline

## Trigger

Use for live browser investigation, WebUI behavior verification, and business-logic confirmation
through the running app — without writing or changing production or test code. Use when the user
wants to confirm what the live app does, discover UI element structure, or verify a cross-surface
user journey.

Do not use for feature implementation, test authoring, or code review. Those route through
`feature-change`, `test-change` within a feature pipeline, or `code-review` respectively. When
browser investigation is needed as a sub-step within a running feature-change, ui-change, or
test-change context, `playwright-cli` is invoked inline by the owning skill — this pipeline
applies only when investigation is the sole stated goal.

## Prerequisites

Confirm each server responds to a health check before proceeding. Do not start servers.

| Service | URL | Health check |
|---|---|---|
| Web UI (React/Vite dev) | `http://localhost:3000` | HTTP 200 at root |
| REST API (FastAPI/uvicorn) | `http://127.0.0.1:7152` | HTTP 200 at `/health` or `/` |

If only the REST API needs verification, the WebUI server may be omitted. If either required
server is unreachable, report the URL, the error, and stop the pipeline.

## Conditional Gates

- Do not modify canonical task data files (`.taskpilot/` YAML and Markdown items) or source
  files via browser automation.
- Do not perform or retry destructive, submitting, or state-mutating actions without explicit user
  approval.
- If the verification goal stated in step 1 is underspecified, ask the user to clarify the target
  URL or behavior before proceeding; do not return to the manager.
- If a code-change goal is introduced at any point during the pipeline, stop, do not implement the
  change, and return control to the manager for routing through the appropriate pipeline.
- If step 2 or step 3 is blocked or fails, stop and return control to the manager.

## Ordered Steps

1. State the verification goal and scope: which URL or surface, which behavior or element structure,
   and what evidence will confirm or deny the goal. List one row per verification target.
2. Run `playwright-cli` with targeted browser steps, following `.claude/conventions/testing.md`
   for snapshot, ref, and re-snapshot practices. Require `Skill: playwright-cli - output below`.
3. Summarize the evidence: for each verification goal stated in step 1, record the evidence source
   (artifact path, snapshot ref, or screenshot), assign status `CONFIRMED_FROM_LIVE_UI` (observed
   directly from the running app) or `UNKNOWN` (observation could not be made), and note the reason
   for any `UNKNOWN` finding.

The manager owns task-complete.

## Output Contract

Begin with `Pipeline: browser-verify - output below` and report:

| Field | Content |
|---|---|
| Status | `completed` — all goals confirmed or explained; `partial` — all goals attempted but one or more remain `UNKNOWN`; `blocked` — a step could not run |
| Servers | URL and reachability status for each server used |
| Verification Goals | One row per goal: goal description, evidence source, and `CONFIRMED_FROM_LIVE_UI` or `UNKNOWN` |
| Handoffs | Completed artifact labels for steps 2–3 |
| Blockers | Failed steps, unreachable servers, or missing evidence |
