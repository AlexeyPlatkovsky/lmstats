---
name: maintain-instruction-system
description: Implements an explicitly approved TaskPilot instruction-system change while preserving authority, routing, layer purity, and narrow scope.
---

# Maintain Instruction System

1. Read `AGENTS.md`, `.claude/skills/manager/SKILL.md`, directly affected runtime artifacts, and
   `.claude/conventions/documentation-quality.md`, plus the applicable standards under
   `.manifesto/conventions/`.
2. Restate the approved change, affected authority owners, and expected output contracts.
3. Modify only the smallest coherent set of root, manager, pipeline, skill, agent, convention,
   adapter, or AI-reference files.
4. Keep framework stages under `.manifesto/` separate from project runtime routing unless
   the user explicitly requests a framework-source update.
5. Synchronize the root registry, manager routes, pipeline references, docs index, and adapters
   whenever paths or capabilities change.
6. Inspect the diff for duplicated authority, missing references, cross-layer leakage, and stale
   paths.

Stop before an unapproved capability deletion, authority relocation, root-model change, or
behavioral contract choice.

The artifact begins with `Skill: maintain-instruction-system - output below` and reports status,
approved scope, changed artifacts, synchronized references, assumptions, checks, and blockers.
