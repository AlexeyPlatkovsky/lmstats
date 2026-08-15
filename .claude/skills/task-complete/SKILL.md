---
name: task-complete
description: Closes non-trivial routed work only after every planned routed artifact is present. Does not apply to trivial direct work.
---

# Task Complete

Report actual execution. Do not redesign or reopen routing.

Before closure, verify every planned routed handoff has its visible output artifact. Raw tool output
does not qualify. If any artifact is missing, blocked, or failed, report closure blocked and name
the artifact; do not declare completion.

Begin with `✅ Skill: task-complete - output below`.

Use exactly this three-column table:

| Step | Skill / Agent | Comment |
|------|---------------|---------|

Include every planned and executed step. Include skipped or blocked steps and explain why. For each
routed handoff, reference its artifact label or transcript location in `Comment`.
