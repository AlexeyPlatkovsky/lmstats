# Changelog

## 0.10.2

### Fixed
- Publish retry logic: `scripts/should-publish.mjs` now checks the npm registry even when the version did not change from the previous commit, allowing a failed publish to be retried by a follow-up fix push.

## 0.10.1

### Fixed
- CLI help and usage now correctly display `lmstats` instead of the old `lm-speed-viewer` executable name.
- Removed stale `lm_speed_viewer.egg-info` build artifact left over from the pre-rename package.

### Added
- `lmstats --version` and `lmstats -v` print the installed package version.
- `lmstats --update` updates the globally-installed npm package via `npm install -g lmstats`.

### Changed
- Renamed remaining internal references from `LM Speed Viewer` / `lm-speed-viewer` to `LM Stats Viewer` / `lmstats` across agent skills, TaskPilot metadata, and the CI report marker.

## 0.10.0

### Changed
- Completed the project rename: Python package, modules, CLI entry point, and all internal references are now `lmstats`.
- `bin/lmstats.js` replaced `bin/lm-speed-viewer.js` as the npm wrapper.
- Kept top-level compatibility modules `app.py` and `db.py` for existing imports.

## 0.9.0

### Added
- ESLint and Stylelint configuration plus UI lint checks in CI.
- npm distribution tests and version-bumping utilities.

### Fixed
- Frontend timestamp trimming bug that could corrupt history display.

### Changed
- npm package name changed from `lm-speed-viewer` to `lmstats`.
- README refreshed with new screenshots and install instructions.

## 0.2.0

### Added
- SQLite persistence for completed predictions (`~/.lmstats/history.db`).
- History API endpoint (`/api/history`) with time-range aggregation.
- Interactive history graph in the dashboard with range selectors and model legend.
- npm packaging: global install via `npm install -g lm-speed-viewer`.
- Automated npm publish workflow.
- CI checks for Python tests, coverage, and UI lint.

### Changed
- Major dashboard redesign and UI stabilization.
- Refactored parser and collector to support durable history.

## 0.1.0

### Added
- Initial release: passive LM Studio generation speed viewer.
- Real-time tok/s dashboard via `lms log stream`.
- SSE streaming and basic web UI on `http://127.0.0.1:8765`.
- Parser for LM Studio log events.
