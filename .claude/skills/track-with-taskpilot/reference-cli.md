# TaskPilot CLI and Direct-File Reference

Command syntax and direct-file fallback procedures for
`.claude/skills/track-with-taskpilot/SKILL.md`. That skill owns the grounding gate, error handling,
and output contract; this file owns command/YAML mechanics only.

## Query tasks via CLI

```sh
# List all items
taskpilot item list

# List items filtered by status
taskpilot item list --status backlog

# List items filtered by type
taskpilot item list --type task

# Show a single item
taskpilot item show TP-3

# JSON output (for programmatic use)
taskpilot --json item list
taskpilot --json item show TP-3
```

## Create a new task

```sh
taskpilot item create \
  --title "Brief title" \
  --type task \
  --priority normal \
  --status backlog \
  --description "Optional details"
```

Required fields: `--title`, `--type`. Returns the new item id (e.g. `TP-6`).

## Update a task

```sh
taskpilot item update TP-3 --status in_progress --priority high
```

Only passed fields are changed. The `updated_at` timestamp is refreshed automatically.

## Comment on a task

```sh
taskpilot item comment TP-3 \
  "needs triage: no match for --ask-for-approval in src/; user confirmed without new evidence" \
  --author claude
```

Both `item_id` and the comment body are required; `--author` defaults to the local user. Returns
the new comment filename. This is the sanctioned path for the `needs triage` marker the grounding
gate requires on a confirmed-without-evidence write; `ground-request` owns what the body must name.

## Read tasks via direct file access

When `taskpilot` is not on PATH, returns exit code 127/not-found, or raw YAML is needed,
read files directly:

- `.taskpilot/items/<ID>.yaml` — single item
- `.taskpilot/items/` — all items

## Create/update tasks via direct file access (CLI fallback)

When the CLI is unavailable and you need to write, create or update a YAML file directly
following the schema at `.taskpilot/items/<existing-id>.yaml`:

```sh
# Write a new item file. Keep the delimiter quoted so nothing in the body expands, then substitute
# the timestamp afterwards. Writing "$(date ...)" inside the body would be stored literally and
# fail canonical ISO validation.
cat > .taskpilot/items/<NEW_ID>.yaml << 'EOF'
schema_version: 1
id: <NEW_ID>
title: 'Item title'
priority: normal
type: task
status: backlog
created_at: '__NOW__'
updated_at: '__NOW__'
description: |
  Free text. Multi-line is safe here because the delimiter is quoted.

  Open Questions
  - recorded per gap disclosure when the request leaves material gaps
EOF
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
sed -i '' "s/__NOW__/$NOW/g" .taskpilot/items/<NEW_ID>.yaml

# Update an existing item's status. The CLI refreshes updated_at automatically; this fallback
# must rewrite it explicitly or the item is left with stale metadata.
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
sed -i '' -e 's/^status: .*/status: done/' \
          -e "s/^updated_at: .*/updated_at: '$NOW'/" .taskpilot/items/TP-3.yaml
```

The quoted delimiter is what makes this safe: title and description text taken from a user request
may contain `$`, backticks, or `\` without being expanded or executed. Never unquote it to
interpolate a value directly — use a placeholder and substitute afterwards, as with `__NOW__`
above.

Comments are one Markdown file per comment under `.taskpilot/comments/<ITEM_ID>/`, named
`YYYY-MM-DDTHH-MM-SSZ.md` — the canonical ISO timestamp with colons replaced by hyphens, matching
`iso_to_filename_stamp` in `src/taskpilot/core/timestamps.py`. The stem must equal
`iso_to_filename_stamp(created_at)`, plus a `-N` suffix starting at `-2` on same-second collision.
Frontmatter carries `schema_version`, `created_at`, and `created_by`, followed by the comment body.
