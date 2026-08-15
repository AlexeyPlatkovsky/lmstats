---
name: taskpilot-cli
description: Uses the local taskpilot CLI to inspect or update this repository's .taskpilot workspace. Use for explicit TaskPilot requests or manager-declared task-backed work; do not edit .taskpilot files directly.
---

# TaskPilot CLI

Run commands from the repository root. First verify the workspace:

```sh
taskpilot validate
taskpilot item list
```

Use the CLI, not direct YAML edits:

```sh
taskpilot item show LMS-1
taskpilot item create --title 'Short title' --type task --priority normal
taskpilot item update LMS-1 --status in_progress
taskpilot item comment LMS-1 'Concise progress note' --author ai
```

Create, rename, describe, or comment on items only when the user explicitly
requests it. For status/priority changes, confirm the item exists first. After
any mutation, run `taskpilot validate` and show the affected item. Report the
command/result and any CLI error; never invent an item ID or edit `.taskpilot/`
as a fallback.
