---
name: design-ui
description: Designs accessible TaskPilot product UI flows and records accepted design decisions. Use before UI implementation; not for marketing pages or production code.
---

# Design TaskPilot UI

Read `designs/design.md`. For WebUI component-library or existing-page work, also read
`.claude/conventions/ui-component-library.md`. This skill designs UI behavior and updates design
docs; production implementation belongs to `implement-change`.

1. Identify the user job, displayed data, primary action, and loading/empty/error/invalid states.
2. Compare the requested UI behavior with accepted specs, roadmap, design docs, and recorded open
   questions. Do not treat UI polish as approval to expand product scope. If the request implies a
   new editable field, new persistence or API behavior, changed release scope, or resolution of an
   open product question, return a scope-delta blocker instead of updating design docs. The blocker
   must state current accepted behavior, requested or implied behavior, why it is a scope change,
   available options, and any recommendation.
3. Reuse existing components and tokens. Without them, use neutral surfaces, one accent, explicit
   hierarchy, and consistent spacing.
4. For existing-page or component-library work, inventory nearby controls and reusable components
   that perform the same job. State whether the change reuses, extends, extracts, or intentionally
   diverges from those patterns.
5. Choose the simplest fitting pattern: table/list for scanning, panel/page for detail, inline
   validation, and explicit status/relation labels.
6. Define the UI interaction contract for every changed control: trigger and selected-value
   display, icon/arrow state, menu/popover placement, hover/selected/focus states, close behavior,
   reset/default behavior, keyboard behavior, focus order, accessible names, and narrow-screen
   behavior.
7. Keep domain and persistence rules out of UI components.
8. Define the component-test and critical E2E coverage required by the design, including finite
   option coverage, sorting indicator states, optimistic/transient states, and browser-only
   behavior where applicable.
9. Create or update `designs/design.md` with accepted flows, patterns, states,
   accessibility behavior, responsive behavior, and unresolved design debt.
10. When a runnable UI already exists, render and inspect desktop and narrow widths to ground the
   design update in observed behavior.

Do not hide validation, file conflicts, sync state, or destructive effects. Do not use color alone
for status or default to decorative dashboards, glass effects, gradients, or gratuitous motion.
If required product behavior, data contracts, or the runnable UI are unavailable, report the
missing context and mark affected design or visual checks blocked rather than inventing them.

Do not modify production UI code while acting in this skill.

The artifact begins with `Skill: design-ui - output below` and reports status, scope-delta result,
flow, layout, component-pattern inventory, interaction contract, states, accessibility,
design-system changes, visual evidence, assumptions, and blockers.
