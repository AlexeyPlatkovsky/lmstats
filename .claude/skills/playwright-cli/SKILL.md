---
name: playwright-cli
description: Verifies LM Speed Viewer browser-visible behavior with playwright-cli at http://127.0.0.1:8765. Use for UI changes or browser investigation; never use it to modify repository files or LM Studio.
---

# Browser Verification

1. Start `python app.py` only when the app is not already running. Do not start,
   stop, or alter LM Studio or `lms`.
2. Open `http://127.0.0.1:8765`; capture a screenshot and accessibility or DOM
   evidence for the requested state.
3. For changed interactions, verify the visible result, empty/error state, and
   live-update behavior when testable without controlling LM Studio.
4. Check a narrow viewport for layout changes. Use stable, user-visible
   locators; do not write app or TaskPilot data through the browser.
5. Record exact commands, URL, evidence, and limitations. Stop the app only if
   this session started it and doing so is safe.

Report pass, fail, or blocked. Browser evidence supplements tests; it does not
replace parser, API, or unit coverage.
