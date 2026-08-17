import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

import { isNewerVersion, nextVersion } from "../../scripts/version-utils.mjs";

const execFileAsync = promisify(execFile);
const projectRoot = join(dirname(fileURLToPath(import.meta.url)), "../..");

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

test("a version bump leaves the versionless README unchanged", async (t) => {
  const fixtureRoot = await mkdtemp(join(tmpdir(), "lmstats-versioning-"));
  const scriptsDirectory = join(fixtureRoot, "scripts");
  const bumpScript = await readFile(join(projectRoot, "scripts/bump-version.mjs"), "utf8");
  const versionUtils = await readFile(join(projectRoot, "scripts/version-utils.mjs"), "utf8");

  t.after(() => rm(fixtureRoot, { recursive: true, force: true }));
  await mkdir(scriptsDirectory);
  await writeFile(join(fixtureRoot, "package.json"), '{\n  "version": "0.9.0"\n}\n');
  await writeFile(join(fixtureRoot, "package-lock.json"), '{"version":"0.9.0","packages":{"":{"version":"0.9.0"}}}\n');
  await writeFile(join(fixtureRoot, "pyproject.toml"), '[project]\nversion = "0.9.0"\n');
  const readme = "# LM Stats Viewer\n\n[![npm version](https://img.shields.io/npm/v/lmstats)](https://www.npmjs.com/package/lmstats)\n";
  await writeFile(join(fixtureRoot, "README.md"), readme);
  await writeFile(join(scriptsDirectory, "bump-version.mjs"), bumpScript);
  await writeFile(join(scriptsDirectory, "version-utils.mjs"), versionUtils);

  await execFileAsync(process.execPath, [join(scriptsDirectory, "bump-version.mjs"), "minor"]);

  assert.match(await readFile(join(fixtureRoot, "package.json"), "utf8"), /"0\.10\.0"/);
  assert.match(await readFile(join(fixtureRoot, "package-lock.json"), "utf8"), /"0\.10\.0"/);
  assert.match(await readFile(join(fixtureRoot, "pyproject.toml"), "utf8"), /"0\.10\.0"/);
  assert.equal(await readFile(join(fixtureRoot, "README.md"), "utf8"), readme);
});
