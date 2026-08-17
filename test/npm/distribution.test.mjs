import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const packageData = JSON.parse(await readFile(new URL("../../package.json", import.meta.url), "utf8"));

test("npm package exposes the Python CLI", () => {
  assert.equal(packageData.name, "lmstats");
  assert.equal(packageData.type, "module");
  assert.deepEqual(packageData.bin, { "lmstats": "bin/lmstats.js" });
});

test("npm package contains source files but not local Python bytecode", () => {
  assert.deepEqual(packageData.files, [
    "bin/",
    "lmstats/*.py",
    "lmstats/static/*",
    "app.py",
    "db.py",
    "pyproject.toml",
    "requirements.txt",
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
  ]);
});

test("npm package and Python distribution use the same version", async () => {
  const pyproject = await readFile(new URL("../../pyproject.toml", import.meta.url), "utf8");

  assert.match(pyproject, new RegExp(`^version = "${packageData.version}"$`, "m"));
});
