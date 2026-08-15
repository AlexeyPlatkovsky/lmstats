# Pencil Design Pipeline

## Trigger

Use for design-only work in Pencil (`.pen` files in `designs/`) with no production code change.
When a single request names both a design goal and a code-change goal, route through
`pen-to-code.md` instead. If this situation is discovered after this pipeline is already loaded,
emit `Pipeline: pen-design — blocked` and return control to the manager for re-routing via
`pen-to-code.md`.

## Prerequisites

Before stage 1:
- Confirm the Pencil MCP server is available (`mcp__pencil__get_editor_state`). Stop if unavailable.
- Confirm `designs/design.md` is readable. Stop if unavailable.
- Confirm the target `.pen` file exists in `designs/`. If it does not exist, create it with
  `Write` using the scaffold `{"version":"2.14","children":[]}`, then ask the user to open it in
  Pencil desktop so it becomes the active editor. Stop if the user cannot open it.

## Ordered Steps

1. **Context load.** Read `designs/design.md` and `docs/design.md`. Search `docs/specs/`
   for a spec related to the work; if one exists, read it. Emit:
   `Pipeline: pen-design — stage 1 context loaded`

2. **Design.** Run `pencil-design` skill. The skill governs all `.pen` file operations including
   shared-component-library discipline, 25-op batch limits, and design-system token alignment.
   Require: `Skill: pencil-design - output below`. Stop if skill reports blocked.

3. **Design review.** Run `design-reviewer` agent in an isolated fresh context. Pass screenshot
   evidence from `mcp__pencil__export_nodes` or `mcp__pencil__get_screenshot` as context.
   Require: `Agent: design-reviewer - output below`.
   - If `design-reviewer` reports blocked, stop and return control to the manager.
   - Critical or High findings → return to stage 2 (`pencil-design`), fix, re-export screenshots,
     re-run `design-reviewer`. Up to 3 loops total. Record loop count and repeat artifact labels.
   - If Critical or High findings remain after 3 loops, stop with blockers.

4. **Snapshot and verify.** Call `mcp__pencil__snapshot_layout()`. Confirm the snapshot is stored
   in `designs/`. If a new reusable component was created, confirm `designs/shared-components-lib.pen`
   has been updated (this is enforced by the `pencil-design` skill's shared-component decision gate).

Stop on a blocked or failed step and return control to the manager. The manager owns
documentation maintenance and task-complete after this pipeline.

## Output Contract

Begin with `Pipeline: pen-design - output below` and report:
- status;
- design file path(s) in `designs/`;
- completed stage labels;
- design-reviewer verdict and loop count;
- snapshot confirmation;
- shared-library update confirmation or N/A;
- blockers.
