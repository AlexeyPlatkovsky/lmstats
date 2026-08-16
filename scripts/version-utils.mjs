const bumps = new Set(["minor", "major", "release"]);

export function versionParts(version) {
  const match = version.match(/^(\d+)\.(\d+)\.(\d+)$/);
  if (!match) {
    throw new Error(`Expected a stable semantic version, got ${version}`);
  }
  return match.slice(1).map(Number);
}

export function nextVersion(version, bump) {
  if (!bumps.has(bump)) {
    throw new Error("Expected one of: minor, major, release");
  }

  let [major, minor, release] = versionParts(version);
  if (bump === "major") {
    major += 1;
    minor = 0;
    release = 0;
  } else if (bump === "minor") {
    minor += 1;
    release = 0;
  } else {
    release += 1;
  }
  return `${major}.${minor}.${release}`;
}

export function isNewerVersion(next, previous) {
  const nextParts = versionParts(next);
  const previousParts = versionParts(previous);

  for (let index = 0; index < nextParts.length; index += 1) {
    if (nextParts[index] !== previousParts[index]) {
      return nextParts[index] > previousParts[index];
    }
  }
  return false;
}
