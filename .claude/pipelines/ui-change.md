# UI Change Pipeline

Use for non-trivial changes to `static/index.html` or its browser-visible
behavior.

1. Inspect the existing page and relevant API/SSE contract; write a concise
   acceptance list covering loading, empty, error, and live-update states.
2. Use `test-change` for parser/API behavior that can prove the UI contract.
3. Use `implement-change` for the smallest accessible HTML/CSS/JS change.
4. Run `validate-change`, then use `playwright-cli` against the running app to
   verify the changed behavior at desktop and a narrow viewport when available.
5. Run `code-reviewer` for medium/high-risk changes and `task-complete`.

Do not add a framework, build system, or design tool unless explicitly asked.
