---
name: track-with-taskpilot
description: Uses TaskPilot as the project task tracker — queries, creates, and updates items via CLI or direct file access to keep work visible and traceable; refuses to write an item whose premise ground-request could not confirm.
user-invocable: true
---

# Track with TaskPilot

## Responsibility

Manage TaskPilot task items for development work during AI-assisted sessions. This skill is a
utility — it is called inline by other skills, routed directly by the manager, or invoked on
demand. The grounding gate below is a hard stop regardless of caller.

## Layer boundary

This skill manages local TaskPilot task items only. Do not use it for:

- Routing or classifying work — use `.claude/skills/manager/SKILL.md`.
- Checking whether a request's premise holds — use `.claude/skills/ground-request/SKILL.md`.
- Implementing production code — use `.claude/skills/implement-change/SKILL.md`.
- Code review or design review — use `.claude/agents/code-reviewer.md` or
  `.claude/agents/design-reviewer.md`.

## Grounding gate

Writing an item title, description, or comment body — whether the text comes from a user request or
from the agent's own analysis — requires a `Skill: ground-request - output below` artifact covering
that content in the current context. This is a precondition on this skill, not an optional step, and
it holds regardless of caller — being invoked inline by a pipeline is not an exemption.

Two exemptions, both narrow. Content derived from an **unqualified** statement in an already-accepted
specification is exempt; a `[planned]`, `[not implemented]`, `[superseded]`, or requirement-register
statement is not unqualified, and `.claude/conventions/documentation-quality.md` owns that test.
Record the exemption in this skill's artifact as `exempt: <spec path and section>` so a downstream
validator can tell an exemption from a skipped gate. The `needs triage` marker below is also exempt,
being grounded by construction.

When the artifact is absent, write nothing, emit this skill's artifact with status `blocked`, and
return control to the manager naming `.claude/pipelines/backlog-change.md`. Do not run
`ground-request` from here: this skill refuses and returns upward; the pipeline owns the ordering.

`ground-request` owns how a premise is checked and what each outcome means. Apply the outcome it
reports per subject:

| Reported outcome | Action here |
| --- | --- |
| `unverified` | Do not write the item; report it as refused. |
| `unverified, user-confirmed` | Write it, and add a `needs triage` comment whose content `ground-request` specifies. |
| `partially grounded` | Write the located state the artifact reports, not the state the request asserted, and report the correction. |
| `grounded` | Write it and cite the reported evidence path. |
| `new scope` | Write it. |

Record any open questions the artifact reports under an `Open Questions` heading in the item
description, so the request is never lost even while its gaps are unsettled.

A refused item does not stop the others: write every permitted item in the request, then report the
refused ones together. This governs item writes only and does not override the batch rule in
`AGENTS.md` for routed task execution.

Updates that touch only technical fields — status, priority, timestamps, links — assert nothing about
repository state and need no grounding artifact.

## Context

This project stores its own tasks in `.taskpilot/items/*.yaml`. The structure:

- `.taskpilot/project.yaml` — project identity (id, key, name)
- `.taskpilot/items/<ITEM_ID>.yaml` — individual items
- `.taskpilot/comments/<ITEM_ID>/` — comment files per item

Each item is a flat YAML file with fields: `schema_version`, `id`, `title`, `priority`
(low|normal|high), `type` (epic|feature|task|bug), `status` (backlog|in_progress|done|cancelled),
`created_at`, `updated_at`, and optional `description`, `parent_id`, `tags`, `created_by`.

## Interactions

Pass user-derived title and description text as single-quoted shell arguments, doubling any
embedded `'`. In YAML use single-quoted scalars (doubling embedded `'`) or a block scalar — never
double quotes, where a lone `\` is an invalid escape and a `"` ends the scalar. After any
direct-file write, re-read the file and confirm it parses and that `created_at` and `updated_at`
are canonical ISO.
Command syntax, direct-file-access fallback, and comment-file naming rules are in
[reference-cli.md](reference-cli.md): CLI query/create/update/comment commands, reading
`.taskpilot/items/` directly, and the quoted-heredoc write procedure for when the CLI is
unavailable.

## Error handling

- **`taskpilot: command not found`** (exit code 127): fall back to direct file access.
- **`.taskpilot/` directory missing**: the workspace has not been initialized — run
  `taskpilot init` or create the directory structure manually per project spec.
- **CLI exit code non-zero**: parse stderr for the error; if it indicates a workspace
  issue, check `.taskpilot/project.yaml` and `.taskpilot/items/` existence.
- **Item file not found**: the item id does not exist — verify with `ls .taskpilot/items/`.

## When to use

- **Before starting work**: check what tasks exist, their statuses, priorities, and types to
  understand the current sprint or backlog context.
- **After completing a task**: update its status to `done`.
- **When starting new work**: create a task item first, then reference the task id in the branch
  name and commit messages.
- **During validation**: verify task-item assertions in the `.taskpilot/` tree match expected
  behavior.
- **When the manager routes work**: if the manager identifies a task-backed item, load this skill
  to verify the item exists and read its current state. Creating a sub-item writes a title and
  description, so the grounding gate applies to it exactly as it does to a user-requested item —
  agent-authored content is ungrounded by construction.

## Output Contract

The artifact begins with `Skill: track-with-taskpilot - output below` and reports:

- status (`completed`, `skipped`, or `blocked`) — `blocked` when any requested write was refused,
  `completed` when every requested write was made (including `partially grounded` corrections and
  `new scope` items carrying open questions), `skipped` when no write was requested or needed;
- invoked operation(s);
- affected item ids;
- the grounding outcome applied per requested item, and the `ground-request` artifact it came from;
  `not required` for a technical-field-only update; or `exempt: <spec path and section>` for a write
  derived from an unqualified accepted-specification statement;
- corrections applied to any `partially grounded` item;
- requested items not written, and the question returned to the user;
- any `needs triage` comment written;
- current item states before and after (if mutated);
- raw YAML snapshot of relevant items (if queried);
- blockers or errors.

Emit the artifact when:
- the caller explicitly includes a directive like "track-with-taskpilot artifact required";
- the operation is part of a routed handoff from the manager or a pipeline;
- the operation mutates item state (create, update);
- any requested write resolves to a grounding outcome other than `grounded`, including refusals
  that write nothing;
- a write was requested and no `ground-request` artifact covers it — status `blocked`.

Do not emit the artifact for unrouted query-only operations that write nothing (e.g. a single
`taskpilot item show` call) unless the caller explicitly requests it. When the manager, a pipeline,
or a calling skill names this skill's artifact as an expected handoff, always emit it — with status
`skipped` when the operation requested no write.
