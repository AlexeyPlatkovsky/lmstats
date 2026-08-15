---
name: maintain-instruction-system
description: Creates or revises this repository's AI-agnostic AGENTS.md, local skills, pipelines, or reviewer prompts. Use only through the manager's instruction-change route.
---

# Maintain Instruction System

1. Read `AGENTS.md`, `.claude/skills/manager/SKILL.md`, and affected artifacts.
2. Keep one routing owner: manager selects routes; pipelines sequence work;
   skills perform a capability; agents review read-only.
3. Remove assumptions about unavailable tools, frameworks, directories, or
   other projects. Prefer project-relative paths and tool-agnostic language.
4. Keep every instruction file below 150 lines, imperative, and narrowly
   scoped. Delete superseded artifacts rather than leave stale alternatives.
5. Verify every referenced file exists and that AGENTS points to manager.

Report changed artifacts, path checks, remaining assumptions, and blockers.
