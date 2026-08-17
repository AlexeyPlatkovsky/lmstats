#!/usr/bin/env node
import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const packageRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const packageVersion = JSON.parse(readFileSync(join(packageRoot, "package.json"), "utf8")).version;
const venvRoot = process.env.LMSTATS_VENV || join(homedir(), ".lmstats", "venvs");
const venv = join(venvRoot, packageVersion);
const isWindows = process.platform === "win32";
const scriptsDirectory = isWindows ? "Scripts" : "bin";
const executable = join(venv, scriptsDirectory, isWindows ? "lmstats.exe" : "lmstats");

function run(command, args) {
  const result = spawnSync(command, args, { stdio: "inherit" });
  if (result.error) {
    return false;
  }
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
  return true;
}

function findPython() {
  for (const candidate of isWindows ? ["py", "python"] : ["python3", "python"]) {
    const versionCheck = spawnSync(
      candidate,
      [...(isWindows && candidate === "py" ? ["-3"] : []), "-c", "import sys; sys.exit(sys.version_info < (3, 10))"],
      { stdio: "ignore" },
    );
    if (!versionCheck.error && versionCheck.status === 0) {
      return candidate;
    }
  }
  console.error("LM Stats Viewer needs Python 3.10 or newer. Install Python and try again.");
  process.exit(1);
}

const python = findPython();
const pythonArgs = isWindows && python === "py" ? ["-3"] : [];

if (!existsSync(executable)) {
  console.log(`Installing LM Stats Viewer ${packageVersion} into ${venv}...`);
  run(python, [...pythonArgs, "-m", "venv", venv]);
  run(join(venv, scriptsDirectory, isWindows ? "python.exe" : "python"), [
    "-m",
    "pip",
    "install",
    "--disable-pip-version-check",
    "--no-input",
    packageRoot,
  ]);
}

const result = spawnSync(executable, process.argv.slice(2), { stdio: "inherit" });
if (result.error) {
  throw result.error;
}
process.exit(result.status ?? 1);
