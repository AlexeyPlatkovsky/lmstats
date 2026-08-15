---
name: manager
description: Classifies and routes every non-trivial TaskPilot task to the correct pipeline, skill, or agent before execution.
user-invocable: false
---

# TaskPilot Work Manager

## Responsibility

Route non-trivial work only. Do not implement, review, test, or document changes in this file.

## Classification

Classify before edits:

- Complexity: trivial or non-trivial.
- Size: small, standard, or major.
- Risk: low, medium, high, or system-level.
- Reach: single area or cross-layer.
- Change type: feature, bug fix, refactor, UI, documentation, review, instruction, or brainstorm.
- Task backing: a task is task-backed only if the user supplies a valid task ID or a canonical
  TaskPilot item exists for the work. All other tasks are untracked.
- Run the three scans defined in `.claude/conventions/classification-scans.md` — product-scope,
  specification-materiality, and architecture-boundary — before finalising the route. That file
  owns each scan's procedure and is the sole owner of the specification-materiality question;
  `docs/specs/README.md` points there rather than restating it. Record each scan's outcome (and,
  for the specification-materiality scan, the settling clause) in this skill's output artifact.

Treat the task as non-trivial when it changes behavior, contracts, persistence, architecture,
production dependencies, or requires more than one coordinated capability.

Size definitions (choose the highest that applies):

1. **Small** — every condition must hold:
   - localized to one file or module;
   - low risk (no data loss, no contract change);
   - expected behavior already explicit in an accepted spec;
   - no public contract, persistence schema, canonical format, cross-layer boundary,
     or multi-step workflow change.

2. **Standard** — any condition may apply but none is high-risk:
   - non-trivial production change with bounded scope;
   - one primary task or behavior;
   - no high-risk architecture, persistence, or canonical-format decision.

3. **Major** — at least one condition applies:
   - cross-layer (touches two or more of core, services, cli, server, web);
   - multi-feature or multi-task;
   - high-risk (data loss, contract break, security);
   - changes a public contract, persistence schema, or canonical format;
   - broad UI workflow crossing screens or browser state;
   - work that needs multiple independent review gates.

## Route Selection

- Feature or non-trivial behavior-changing bug fix: `.claude/pipelines/feature-change.md`.
- Behavior-preserving refactor: `.claude/pipelines/refactor-change.md`.
- Product UI implementation, existing-page UI changes, or local WebUI component-library work not
  explicitly handled by an MCP design route: `.claude/pipelines/ui-change.md`.
- Design-only work in Pencil (`.pen` files in `designs/`) without production code change:
  `.claude/pipelines/pen-design.md`. `.pen` file work is always non-trivial (UI contracts, design
  review required). Before routing here, confirm the Pencil MCP is available.
- Converting an accepted Pencil design to tested React code: `.claude/pipelines/pen-to-code.md`.
  Before routing here, confirm the `.pen` file exists in `designs/` and an accepted spec or
  explicit acceptance criteria is present.
- Live browser investigation, WebUI verification, or business-logic confirmation without code
  changes: `.claude/pipelines/browser-verify.md`. When browser investigation is requested as a
  sub-step within a running feature-change, ui-change, test-change, or validate-change context,
  `playwright-cli` is called inline by the owning skill — `browser-verify.md` applies only when
  investigation is the sole stated goal. Mid-session code-change requests during a browser-verify
  run return control to the manager. When a single request names both an investigation goal and a
  code-change goal, treat the request as non-trivial and route through the appropriate
  feature-change, test-change, or ui-change pipeline, invoking `playwright-cli` inline.
- Creating, updating, or fixing functional Playwright E2E tests, Page Objects, E2E support helpers,
  `data-test-id` hooks, or E2E CI behavior: `.claude/pipelines/e2e-change.md`.
- Read-only instruction-system review: `.claude/agents/instruction-evaluator.md`.
- Instruction-system review with iterative fix loop: `.claude/pipelines/instructions-review.md`.
- Other read-only review request: `.claude/pipelines/code-review.md`.
- Open high-impact choice with materially different outcomes: `.claude/skills/brainstorm/SKILL.md`.
- Documentation-only work: `.claude/skills/maintain-docs/SKILL.md`, then validation and completion.
- Creating a TaskPilot task, feature, epic, or bug item, updating an existing item's title or
  description, or writing a comment body: `.claude/pipelines/backlog-change.md`.
- Read-only TaskPilot queries, and updates that touch only technical fields (status, priority,
  timestamps, links): `.claude/skills/track-with-taskpilot/SKILL.md`.
  Take either route only when the request explicitly references the project's own TaskPilot workspace
  (``.taskpilot/``). If the request is about a different project or task system, stop and report that
  these routes only manage the local TaskPilot workspace.
- Project instruction-system creation or material change: `.claude/pipelines/instruction-change.md`.

When a single request names both a task-tracking operation and a non-tracking work goal, treat
the full request as non-trivial and route through the appropriate feature-change, test-change, or
ui-change pipeline (whichever matches the non-tracking part), invoking ``track-with-taskpilot``
inline through that pipeline's implementation skill for technical-field updates only.

When the request also writes an item title, description, or comment body, split it: route that write
through ``.claude/pipelines/backlog-change.md`` as a separate ordered handoff, before or after the
code route, and name both that pipeline and ``Skill: ground-request - output below`` among the
expected handoffs. Do not fold the write into the code route's implementation skill — that skill
refuses it and returns control here, and the write would bypass the backlog-change validation gates.

Framework stages under `.manifesto/`, including `02_review.md`, are invoked explicitly by
the user. They are framework workflows, not project routing targets.

Use conditional rigor:

- Small low-risk changes may stay on the current branch, skip task movement, skip a new
  specification when the specification-materiality scan exempts them, and validate with focused
  tests and checks.
- Standard or major task-backed feature work requires a fresh branch through `work-with-git` before
  implementation, unless the user explicitly overrides it or branch creation is blocked. The manager
  must state the branch source, branch name, and whether task-state hygiene is required before
  `work-with-git` runs.
- Major or high-risk feature work requires tests before implementation and independent review of
  the test scope before production changes.
- Refactors require characterization tests first when existing coverage does not prove preserved
  behavior.
- UI work requires component coverage, functional E2E coverage for major paths, and separate
  browser contract evidence for style/token/browser behavior when required by
  `.claude/conventions/testing.md`.
- UI work that creates or changes a reusable component, replaces a native browser control, changes
  drag/drop behavior, changes optimistic/cache-visible state, or changes a shared interaction
  pattern is at least medium risk unless it is documentation-only. Do not classify those changes as
  low risk merely because the code is localized.
- The local WebUI component library is the default implementation source for TaskPilot UI changes.
  Pencil remains the selected MCP route when the user explicitly asks for Pencil, `.pen` files, or
  an existing `.pen` design.

For high-risk or system-level work, require independent review after validation. For medium-risk
production work, require independent review unless the change is documentation-only. For
`code-reviewer` and `design-reviewer` findings with Critical, High, or Major severity, require
fixes and re-review for up to three loops or stop with blockers. Severity definitions are owned by
`.claude/conventions/review-severity.md`. Agents with canonical verdict contracts, such as
instruction-system review agents, keep their own stop and retry rules. Each code/design review loop
returns to the responsible previous capability, reruns required validation, reruns the same
reviewer, and records the attempt count plus repeated artifact labels.

## Handoff Gate

Name every selected capability and expected artifact before execution. Do not advance when an
expected artifact is absent or reports blocked/failed status. Raw tool output is not a substitute.

When the manager selects a pipeline, that pipeline must be loaded and its first artifact emitted
before any implementation begins. Do not proceed directly to implementation even when tasks are
clearly defined.

When implementation changes behavior, interfaces, commands, architecture, domain facts, project
structure, or known failure modes, append documentation maintenance after substantive work.

Append task-complete to every non-trivial route. Before invoking it, verify every planned artifact
is present.

## Output Contract

Begin with:

`Manager: taskpilot-manager - output below`

Include:

- status;
- complexity, risk, and reach;
- size and change type;
- task backing;
- branch decision: fresh branch required or skipped, branch source and branch name or `N/A` when
  skipped, and reason;
- task-state decision: required or skipped, target task item when known, sanctioned update path,
  verification evidence required, and reason;
- product-scope delta: none, or list deltas and required user decisions;
- specification-materiality decision: required or exempt, and the clause that settled it;
- architecture-boundary scan outcome: no violation, or each violating cross-layer import and its
  blocker/non-blocker disposition;
- selected pipeline or immediate capability;
- ordered handoffs and exact expected artifact labels;
- validation and independent-review requirements;
- documentation-maintenance decision;
- final task-complete step;
- assumptions and blockers.
