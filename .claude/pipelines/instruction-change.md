# Instruction Change Pipeline

Use for creating or materially changing `AGENTS.md`, `.claude/skills/`,
`.claude/pipelines/`, or `.claude/agents/`.

1. Read `AGENTS.md`, the manager, and all directly affected artifacts.
2. Run `maintain-instruction-system`; preserve one owner for routing and keep
   every instruction file under 150 lines.
3. Check paths, frontmatter, duplication, and stale product assumptions.
4. Run a fresh read-only pass using `code-reviewer`; if subagents are not
   available, apply its checklist separately.
5. Run `task-complete` and report the files changed and checks run.

Stop for an unclear authority boundary or a requested workflow that this
repository cannot support.
