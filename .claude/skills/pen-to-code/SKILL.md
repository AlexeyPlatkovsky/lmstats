---
name: pen-to-code
description: Reads a Pencil .pen design file and produces a component specification for test-first React implementation. Does not write code or tests.
applies_when: translating an accepted .pen design into a React component specification
---

# Pen-to-Code Translation Skill

## Purpose

Extract the component contract from a Pencil `.pen` frame and emit a specification that the
`test-change` and `implement-change` skills can execute without further design interpretation.
This skill reads; it never writes production code, test files, or CSS.

## Visible-Artifact Trace

Emit before the first tool call:

`Trace: skill pen-to-code — output below`

## Prerequisites

Before executing:
1. Confirm the target `.pen` file exists in `designs/`. Stop if absent.
2. Confirm an accepted spec or explicit acceptance criteria is present for the work. Stop if absent.
3. Confirm the Pencil MCP server is available. Stop if unavailable.

## Execution Steps

1. **Load design context.** Read `designs/design.md` (Required States, Accessibility
   Baseline, Visual Direction, Color Tokens, Icon Library sections) and `docs/design.md`.

2. **Read the design.** Call in order:
   - `mcp__pencil__get_editor_state(include_schema: true)` — load current schema.
   - `mcp__pencil__batch_get` — retrieve top-level nodes to enumerate available frames.
   - Confirm the named target frame exists in the file. If it is not found, stop and report the
     available frame names so the user can supply the correct one.
   - `mcp__pencil__get_variables()` — load design variables/tokens.
   - `mcp__pencil__export_html(targetFrame)` — structural reference only; not production code.

3. **Extract component inventory.** For each visible component and sub-component:
   - Name: kebab-case, prefixed `component/` if reusable (e.g., `component/status-badge`).
   - Inferred TypeScript props interface.
   - States visible in the frame (loading, empty, error, populated, hover, disabled, invalid, etc.).
   - Layout description using token references (`--space-4`, `--radius-md`, etc.).
   - Color mapping: each fill/stroke → the corresponding `tokens.css` token.
   - Interactive affordances: click targets, keyboard behavior, focus order.
   - Required Lucide icons with `aria-label` values.

4. **Gap analysis.** Compare visible states against the Required States list from
   `designs/design.md`. List every required state absent from the frame.
   Also report any token gap (a visual value that has no mapping in `web/src/tokens.css`) with a
   proposed token name and value range.
   Stop and present both gap lists to the user before emitting the component specification. Await
   user decision: confirmed gaps (states intentionally out of scope, approved token proposals)
   allow continuation; unresolved gaps remain blockers.

5. **Emit component specification.** For each component in scope:

   ```
   Component: <ComponentName>
   File: web/src/components/<ComponentName>.tsx
   CSS module: web/src/components/<ComponentName>.module.css

   Props interface (TypeScript):
   <interface block>

   Accessibility contract:
   - ARIA role: <role>
   - Keyboard behavior: <description>
   - Accessible name source: <prop or aria-label strategy>

   Required states:
   - <state>: <rendering description>
   - ...

   CSS classes and token assignments:
   - .<className>: background var(--token), color var(--token), ...
   - ...

   Test coverage targets:
   - renders in <state> state: <assertion>
   - accessible name is <value>: <assertion>
   - ...
   ```

## Stop Conditions

- Target `.pen` file absent from `designs/` → stop, report path.
- Pencil MCP unavailable → stop.
- Accepted spec or acceptance criteria absent → stop.
- Named target frame not found in the `.pen` file → stop, report available frame names.
- Required states absent from frame or token gaps identified → stop and present the gap list to
  the user before proceeding. Await user decision. Confirmed gaps (intentionally out of scope or
  approved token proposals) allow continuation; unresolved gaps remain blockers.

## Output Contract

Begin with: `Skill: pen-to-code - output below`

Include:
- status (complete, blocked);
- `.pen` source file and frame name;
- component count;
- full specification for each component;
- gap list (missing required states, token gaps) — empty if none;
- blockers.
