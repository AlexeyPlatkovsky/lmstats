# Backlog Change Pipeline

## Trigger

Use when creating a TaskPilot task, feature, epic, or bug item, when updating an existing item's title
or description, or when writing a comment body — whether the content comes from a user request or from
the agent's own analysis. Do not use it for read-only queries, or for updates that touch only
technical fields — status, priority, timestamps, links — which stay a direct `track-with-taskpilot`
call.

A mixed request that names both a tracking write and a code goal splits. This pipeline owns the
title, description, or comment-body write and runs before or after the code route; the inline
`track-with-taskpilot` call inside another pipeline's implementation skill is limited to
technical-field updates. Without the split, the item write would land outside step 5's gates.

## Conditional Gates

`ground-request` owns the **gap** and **defect** vocabulary used below.

- When `ground-request` reports a documentation defect, run `maintain-docs` before the item writes.
  Require `Skill: maintain-docs - output below`.
- When `ground-request` reports only a documentation gap, run `maintain-docs` after the item writes.
  Require `Skill: maintain-docs - output below`.
- Skip `maintain-docs` when `ground-request` reports neither a gap nor a defect.
- A `maintain-docs` run that corrects a defect returns to `ground-request` for the affected subjects
  before the writes, and records the repeated artifact label. Repeat at most twice, then stop with a
  blocker.

## Ordered Steps

1. Run `ground-request` for every subject the request asserts. Require
   `Skill: ground-request - output below`.
2. Run `maintain-docs` when a conditional gate places it before the writes. Require
   `Skill: maintain-docs - output below`.
3. Run `track-with-taskpilot` for the item and comment-body writes. Require
   `Skill: track-with-taskpilot - output below`.
4. Run `maintain-docs` when a conditional gate places it after the writes. Require
   `Skill: maintain-docs - output below`.
5. Run `validate-change` against the final diff, gating on each of: every written item cites the
   evidence path `ground-request` reported; no item file exists for a refused subject; every
   `partially grounded` correction is present in the written text rather than the asserted text;
   every write made on user confirmation without new evidence has its `needs triage` comment file;
   every reported open question appears under `Open Questions` in the item it belongs to; and every
   written item file parses with canonical ISO timestamps. Require
   `Skill: validate-change - output below`.

When every requested subject resolves to `unverified`, the pipeline stops at step 1 and returns
control to the manager. When some subjects are writable — `grounded`, `partially grounded`, or
`new scope` — and others are refused, continue through the remaining steps for the writable ones and
report the refusals. Stop on any other blocked or failed
step and return control to the manager. The manager owns task-complete.

When the user answers a refused subject, re-enter at step 1 with their answer as a recorded input. A
restatement that supplies new evidence is grounded normally. A confirmation that supplies no new
evidence resolves the subject at step 1 as `unverified, user-confirmed`, without a second identical
search, and resumes at step 3 carrying its `needs triage` requirement — re-running the same search
against unchanged source would only return `unverified` again and bounce the request indefinitely.

This pipeline writes only under `.taskpilot/` and, through `maintain-docs`, under `docs/`. It does not
create or retire `docs/features/` folders, so it never resyncs `docs/INDEX.md`.

## Output Contract

Begin with `Pipeline: backlog-change - output below` and report status, item ids written and refused,
the grounding outcome per subject, documentation actions taken and their placement relative to the
writes, open questions returned to the user, repeated artifact labels, deviations, and blockers.
