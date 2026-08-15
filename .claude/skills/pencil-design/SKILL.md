---
name: pencil-design
description: Creates and edits UI/UX designs in Pencil via its MCP server. Use for design-only requests. Do not implement application code for design-only tasks.
applies_when: creating or modifying wireframes, mockups, or UI designs in .pen files
---

# pencil-design

## Purpose

Execute design work for TaskPilot using the Pencil MCP server. This skill reads and writes `.pen` files, applies design system guidelines, and produces validated design artifacts.

This skill is pure execution. It does not choose design directions (`brainstorm` does that), does not orchestrate validation (the `ui-change` pipeline does that), and does not report closure (`task-complete` does that).

## What Is Pencil

[Pencil](https://pencil.dev) is a UI/UX design tool for creating web and mobile mockups. Designs are stored as `.pen` files — JSON documents with a `"version": "2.14"` field. Read and editing of design content must go through Pencil MCP tools, not `Read` or `Grep`. New blank files can be created with `Write` using the minimal scaffold `{"version":"2.14","children":[]}`.

## Prerequisites

The Pencil MCP server must be installed, configured, and running in your Claude Code settings. Verify availability by confirming Pencil MCP tools such as `get_editor_state` and `get_guidelines` are callable. If they are unavailable, stop and ask the user to configure the Pencil MCP server before continuing.

## Hard MCP Limitations

These are protocol-level constraints. Do not attempt to work around them; violations produce silent
data loss.

1. **File creation.** Pencil MCP cannot create `.pen` files. Use the `Write` tool with the minimal
   scaffold `{"version":"2.14","children":[]}` to create new files on disk before populating them
   via `batch_design`.

2. **Active-editor-only writes.** `batch_design` writes to the file reported by `get_editor_state`,
   not to `filePath`. The `filePath` parameter selects variable/import scope for reads only. To
   populate a specific `.pen` file, the user must open it in Pencil desktop; then call
   `get_editor_state` to confirm the active editor changed before writing.

3. **Unified canvas.** All `.pen` files under `designs/` share one design space. Opening any file
   reveals the same combined content. Individual files act as entry points, not isolated containers.
   Do not rely on per-file isolation.

4. **Before every multi-file task, check `get_editor_state`** to confirm which file is active.
   If the active file does not match the intended target, report the mismatch and ask the user to
   switch files in Pencil.

---

## Execution Rules

### 1. Load required context

- Read `designs/design.md` and `docs/design.md` before opening any `.pen` file. These are the only visual policy sources for tokens, naming, components, panel order, and layout conventions.
- Start Pencil work with:

```
get_editor_state(include_schema: true)
```

- Never read `.pen` files as plaintext; use Pencil MCP only.
- Store project design files under `designs/` with kebab-case names.
- Call `get_guidelines()` and load only the relevant Pencil guide/style.

**Constraints checkpoint — read these before touching the canvas:**

Read `designs/design.md` § Visual Direction and Core Patterns and enumerate the active "Do not" constraints for this session. Do not proceed from memory; read the live source. Any design operation that would violate these constraints must stop, present 2–3 options with trade-offs, and wait for approval.

**Stop triggers — halt before executing any `batch_design` call, then present 2–3 options and wait for approval:**
- A token, component, spacing value, or layout rule needed for the task is not in `designs/design.md`.
- A hardcoded value is about to be introduced where a documented token exists.
- A new component would be created that duplicates an existing one in the library (return to the §3 decision gate first — check for variants before halting).
- A frame requires a new interaction state, breakpoint behavior, or layout pattern not covered by `designs/design.md`.

For ambiguous decisions within the documented system (e.g., choosing between two valid token values), pick the nearest match, record it as an inferred decision, and continue.

### 2. Inspect before editing

For existing `.pen` files:
- list top-level nodes with `batch_get`
- read the target subtree before modifying it
- combine searches in one `batch_get` call when possible
- inspect variables and reusable components before introducing new values or structure

```
batch_get({ reusable: true })
```

### 3. Shared component library

The canonical shared component source is `designs/shared-components-lib.pen`. Read `designs/design.md` § "Icon Library" for the current icon inventory; component inventory is maintained in the `.pen` file itself.

**Before creating any new component — work through this decision gate in order:**
1. Search the open file for an existing reusable component (`batch_get({ reusable: true })`).
2. If a similar component exists, ask: can the needed variation be expressed as a `--modifier` or `__part` on the existing component without forking it? If yes, add the variant; do not create a new component.
3. If no match in the file, check `shared-components-lib.pen` for a canonical version.
4. If the component exists in the library but not in the current file, copy its structure into the current file as a new `reusable: true` frame named `component/<name>`.
5. If the component does not exist anywhere, create it in `shared-components-lib.pen` first, then copy it into the destination file.

Never skip steps 1 and 2. Variant proliferation is the primary source of design-system debt.

**Rule: any element present in 2 or more `.pen` files must be defined in `shared-components-lib.pen`.**

**Sync workflow when updating a shared component:**
1. Edit the component in `shared-components-lib.pen`.
2. Open each destination file; update its local `component/` copy to match.
3. Instances within each file automatically reflect the updated local component.

**Cross-file auto-propagation** is not available via MCP. The Pencil UI "Turn into library" + Libraries panel import unlocks it, but requires a one-time manual step per file. Until that is done, syncing is manual per the workflow above.

**Component naming:** always prefix with `component/` (e.g. `component/task-card`, `component/status-badge`). This makes reusable components identifiable in `batch_get` searches.

### 4. Execute with design-system discipline

- Use documented tokens and existing Pencil variables for repeated color, type, spacing, radius, and surface values.
- Reuse existing components before creating new structures; prefer component copies when an equivalent component exists.
- Name meaningful nodes with business-semantic kebab-case and preserve panel reading order.
- Name all significant nodes by purpose, not primitive type: "item-detail-modal" not "Frame 3".
- Pencil renders siblings in reverse order in the Layers tab — order bottom-to-top, right-to-left when that matters.
- Keep the tree navigable: no generic leftovers, duplicate ambiguous sibling names, meaningless wrappers, or avoidable nesting.
- Keep temporary token aliases exploration-only; resolve or escalate them before handoff.
- For page-level designs, create or update the desktop frame only. Do not create tablet or mobile frames unless the user explicitly requests them.

### 5. Batch operations efficiently

- Keep each `batch_design` call to **maximum 25 operations**.
- Split large designs into logical sections: document structure first, then frame content, then styling.
- **Never reuse binding names across separate `batch_design` calls.**
- If a call returns issues in the response message, fix them in the very next call before continuing.
- Build structure with `I()` (insert) first, then customize with `U()` (update) — do not nest large object trees into a single `I()`.

### 6. Hand off cleanly

Before returning control to the pipeline, verify semantic names, panel order, token use, reusable components, desktop screenshot/export coherence, and layout health. Page-level designs report desktop coverage; tablet/mobile frames are included in the report only when the user explicitly requested them. This skill does not run pipeline validation or report closure.

---

## Error Handling

If `batch_design` fails, report the error; the failed operation batch is rolled back. If `batch_design` returns warnings, fix them in the next batch before proceeding to broader visual verification.

---

## Pencil MCP Tool Reference

All tools below are MCP server commands provided by the Pencil MCP server.

| Tool | What it does |
| --- | --- |
| `get_editor_state(include_schema=true)` | Returns the current document structure and available node types/properties |
| `batch_get(nodeIds, patterns, parentId, readDepth, ...)` | Reads current properties of one or more nodes or searches by pattern — always inspect before editing |
| `get_guidelines(category, name, params)` | Lists or loads Pencil guides and styles |
| `batch_design(filePath, input)` | Applies JavaScript snippets that create, update, move, replace, or delete nodes |
| `get_screenshot(nodeId)` | Captures a node as an image; use `document` for the whole document |
| `snapshot_layout()` | Records the current layout state for comparison |
| `get_variables()` | Reads design tokens (colors, spacing, typography) |
| `export_nodes(nodeIds, format)` | Exports nodes as PNG, JPEG, WEBP, or PDF |
| `export_html(nodeIds)` | Exports nodes as HTML |

---

## Output Contract

Before this skill's first tool call on its turn, emit one line:

`Trace: skill pencil-design — output below`

At the end of execution, emit:

`Skill: pencil-design - output below`

Then include:

| Field | Content |
| --- | --- |
| Status | `completed`, `skipped`, or `blocked` |
| Target | Document, page, frame, or node area changed |
| Files changed | `.pen` files created or modified |
| Changes made | Design elements created, updated, or deleted |
| Guidelines used | Pencil guidelines, `designs/design.md` sections, or `docs/design.md` sections consulted |
| Verification | `snapshot_layout`, `batch_get`, screenshot path, or reason not run |
| Assumptions / inferred decisions | Material assumptions or inferred design decisions (e.g., "used `space-xl` for section gap — task said 'generous spacing', nearest token was 24px"), or `none` |
| Warnings / Errors | Tool warnings or errors, or `none` |
| Open questions | Clarifications needed, or `none` |
