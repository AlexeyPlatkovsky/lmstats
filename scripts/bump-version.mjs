import { readFile, writeFile } from "node:fs/promises";
import { nextVersion } from "./version-utils.mjs";

const bump = process.argv[2];

if (!new Set(["minor", "major", "release"]).has(bump)) {
  console.error("Usage: node scripts/bump-version.mjs <minor|major|release>");
  process.exitCode = 1;
} else {
  const packagePath = new URL("../package.json", import.meta.url);
  const pythonPath = new URL("../pyproject.toml", import.meta.url);
  const readmePath = new URL("../README.md", import.meta.url);
  const packageData = JSON.parse(await readFile(packagePath, "utf8"));
  const pythonData = await readFile(pythonPath, "utf8");
  const readmeData = await readFile(readmePath, "utf8");
  const pythonVersion = pythonData.match(/^version = "(\d+)\.(\d+)\.(\d+)"$/m)?.[0];
  const readmeHeading = readmeData.match(/^# LM Speed Viewer v(\d+\.\d+(?:\.\d+)?)$/m)?.[0];
  const displayedVersion = packageData.version.endsWith(".0")
    ? packageData.version.slice(0, -2)
    : packageData.version;

  if (!pythonVersion || pythonVersion !== `version = "${packageData.version}"`) {
    throw new Error("package.json and pyproject.toml must start with the same version");
  }
  if (!readmeHeading || readmeHeading !== `# LM Speed Viewer v${displayedVersion}`) {
    throw new Error("README.md heading must start with the package version");
  }

  const version = nextVersion(packageData.version, bump);
  const nextDisplayedVersion = version.endsWith(".0") ? version.slice(0, -2) : version;
  packageData.version = version;
  await writeFile(packagePath, `${JSON.stringify(packageData, null, 2)}\n`);
  await writeFile(pythonPath, pythonData.replace(pythonVersion, `version = "${version}"`));
  await writeFile(
    readmePath,
    readmeData.replace(readmeHeading, `# LM Speed Viewer v${nextDisplayedVersion}`),
  );
  console.log(`Bumped version to ${version}`);
}
