import { execFileSync } from "node:child_process";
import { readFile } from "node:fs/promises";
import { isNewerVersion } from "./version-utils.mjs";

const packageData = JSON.parse(await readFile(new URL("../package.json", import.meta.url), "utf8"));
const previousCommit = process.argv[2];

if (!previousCommit) {
  throw new Error("Expected the previous main commit as the only argument");
}

let previousPackage;
try {
  previousPackage = JSON.parse(
    execFileSync("git", ["show", `${previousCommit}:package.json`], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    }),
  );
} catch {
  previousPackage = undefined;
}

if (previousPackage && !isNewerVersion(packageData.version, previousPackage.version)) {
  console.log("publish=false");
  process.exit(0);
}

try {
  execFileSync(
    "npm",
    ["view", `${packageData.name}@${packageData.version}`, "version", "--registry=https://registry.npmjs.org"],
    { stdio: ["ignore", "ignore", "pipe"] },
  );
  console.log("publish=false");
} catch (error) {
  if (error.stderr?.toString().includes("E404")) {
    console.log("publish=true");
  } else {
    throw error;
  }
}
