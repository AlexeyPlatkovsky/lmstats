---
name: write-e2e-tests
description: Writes or updates TaskPilot functional Playwright E2E tests using Page Objects, data-test-id locators, and explicit TDD level justification.
---

# Write E2E Tests

Read `.claude/conventions/testing.md` and `web/e2e/pages/README.md` when present.

1. State the E2E change phase: tests-first, update, fix, or post-UI-change coverage.
2. Produce an E2E justification table before editing tests:
   requirement or workflow, user-observable assertion, why unit/component/API cannot prove it,
   target functional spec, and target Page Object method.
3. Add or update `data-test-id` attributes in production UI only when the user-facing element has
   no stable existing hook. Attribute names must be kebab-case and domain-oriented.
4. Put every Playwright locator in `web/e2e/pages/` Page Object files. Functional specs under
   `web/e2e/functional/` must not call `page.locator`, `page.getByRole`, `page.getByText`,
   `page.getByLabel`, `page.getByTestId`, `locator(...)`, or equivalent locator constructors.
5. Use `data-test-id` as the primary Page Object selector. Page Objects may use accessible role,
   label, or text locators only as a secondary assertion or when no stable `data-test-id` can be
   added; record that exception in the artifact.
6. Keep specs readable: arrange data or route mocks in support helpers, then call Page Object
   methods for browser actions and assertions.
7. Run the narrow functional E2E command for changed specs, then `npm run test:e2e:functional` from
   `web/`. If UI code changed, also run the normal UI validation gates selected by the manager.
8. Inspect for raw locator usage in specs, selector drift, hidden shared state, broad E2E coverage,
   sleeps, false positives, and missing lower-level-test justification.

Do not change product behavior beyond stable test attributes unless the active route assigns that
scope.

The artifact begins with `Skill: write-e2e-tests - output below` and reports status, phase,
justification table, changed specs, changed Page Objects, changed `data-test-id` hooks, commands and
results, selector exceptions, lower-level coverage rationale, flakiness risks, and blockers.
