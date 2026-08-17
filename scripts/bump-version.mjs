import { readFile, writeFile } from "node:fs/promises";
import { nextVersion } from "./version-utils.mjs";

const bump = process.argv[2];

if (!new Set(["minor", "major", "release"]).has(bump)) {
  console.error("Usage: node scripts/bump-version.mjs <minor|major|release>");
  process.exitCode = 1;
} else {
  const packagePath = new URL("../package.json", import.meta.url);
  const lockPath = new URL("../package-lock.json", import.meta.url);
  const pythonPath = new URL("../pyproject.toml", import.meta.url);
  const packageData = JSON.parse(await readFile(packagePath, "utf8"));
  const lockData = JSON.parse(await readFile(lockPath, "utf8"));
  const pythonData = await readFile(pythonPath, "utf8");
  const pythonVersion = pythonData.match(/^version = "(\d+)\.(\d+)\.(\d+)"$/m)?.[0];

  if (!pythonVersion || pythonVersion !== `version = "${packageData.version}"`) {
    throw new Error("package.json and pyproject.toml must start with the same version");
  }
  if (lockData.version !== packageData.version || lockData.packages?.[""]?.version !== packageData.version) {
    throw new Error("package-lock.json and package.json must start with the same version");
  }
  const version = nextVersion(packageData.version, bump);
  packageData.version = version;
  lockData.version = version;
  lockData.packages[""].version = version;
  await writeFile(packagePath, `${JSON.stringify(packageData, null, 2)}\n`);
  await writeFile(lockPath, `${JSON.stringify(lockData, null, 2)}\n`);
  await writeFile(pythonPath, pythonData.replace(pythonVersion, `version = "${version}"`));
  console.log(`Bumped version to ${version}`);
}
