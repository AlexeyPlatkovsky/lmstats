import assert from "node:assert/strict";
import test from "node:test";

import { isNewerVersion, nextVersion } from "../../scripts/version-utils.mjs";

test("minor, major, and release bumps follow the release policy", () => {
  assert.equal(nextVersion("0.2.0", "minor"), "0.3.0");
  assert.equal(nextVersion("0.2.0", "major"), "1.0.0");
  assert.equal(nextVersion("0.2.0", "release"), "0.2.1");
});

test("only a semantically higher version is publishable", () => {
  assert.equal(isNewerVersion("1.0.0", "0.3.0"), true);
  assert.equal(isNewerVersion("0.3.0", "1.0.0"), false);
  assert.equal(isNewerVersion("0.3.0", "0.3.0"), false);
});
