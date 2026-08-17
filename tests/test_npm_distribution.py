"""Tests for the npm distribution and release tooling."""

import json
import os
from pathlib import Path
import subprocess
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_release_metadata_exposes_the_cli_and_current_version():
    package = json.loads((ROOT / "package.json").read_text())
    with (ROOT / "pyproject.toml").open("rb") as config_file:
        project = tomllib.load(config_file)["project"]
    python_version = project["version"]

    assert package["name"] == "lmstats"
    assert package["version"] == python_version
    readme = (ROOT / "README.md").read_text()
    assert readme.startswith("# LM Stats Viewer\n")
    assert "[![npm version](https://img.shields.io/npm/v/lmstats)]" in readme
    assert package["bin"] == {"lmstats": "bin/lmstats.js"}
    assert project["name"] == "lmstats"
    assert project["scripts"] == {"lmstats": "lmstats.cli:main"}
    assert package["scripts"] == {
        "test": "node --test test/npm/**/*.test.mjs",
        "lint:js": "eslint lmstats/static/app.js",
        "lint:css": "stylelint lmstats/static/styles.css",
        "lint:ui": "npm run lint:js && npm run lint:css",
        "version:minor": "node scripts/bump-version.mjs minor",
        "version:major": "node scripts/bump-version.mjs major",
        "version:release": "node scripts/bump-version.mjs release",
    }


def test_bump_version_keeps_python_npm_and_readme_versions_in_sync(tmp_path):
    project = tmp_path / "project"
    scripts = project / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "bump-version.mjs").write_text((ROOT / "scripts/bump-version.mjs").read_text())
    (scripts / "version-utils.mjs").write_text((ROOT / "scripts/version-utils.mjs").read_text())
    (project / "package.json").write_text('{"name":"lmstats","version":"0.9.0"}\n')
    (project / "package-lock.json").write_text(
        '{"name":"lmstats","version":"0.9.0","lockfileVersion":3,'
        '"packages":{"":{"name":"lmstats","version":"0.9.0"}}}\n'
    )
    (project / "pyproject.toml").write_text('[project]\nversion = "0.9.0"\n')
    readme = "# LM Stats Viewer\n\n[![npm version](https://img.shields.io/npm/v/lmstats)](https://www.npmjs.com/package/lmstats)\n"
    (project / "README.md").write_text(readme)

    for command, expected_version in (
        ("minor", "0.10.0"),
        ("major", "1.0.0"),
        ("release", "1.0.1"),
    ):
        result = subprocess.run(
            ["node", "scripts/bump-version.mjs", command],
            cwd=project,
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stderr
        assert json.loads((project / "package.json").read_text())["version"] == expected_version
        lockfile = json.loads((project / "package-lock.json").read_text())
        assert lockfile["version"] == lockfile["packages"][""]["version"] == expected_version
        with (project / "pyproject.toml").open("rb") as config_file:
            assert tomllib.load(config_file)["project"]["version"] == expected_version
        assert (project / "README.md").read_text() == readme


def test_publish_check_allows_a_new_main_version_missing_from_npm(tmp_path):
    project = tmp_path / "project"
    scripts = project / "scripts"
    fake_bin = tmp_path / "bin"
    scripts.mkdir(parents=True)
    fake_bin.mkdir()
    for filename in ("should-publish.mjs", "version-utils.mjs"):
        (scripts / filename).write_text((ROOT / "scripts" / filename).read_text())
    (project / "package.json").write_text('{"name":"lmstats","version":"0.2.0"}\n')

    for command in (
        ["git", "init", "-q"],
        ["git", "config", "user.email", "test@example.com"],
        ["git", "config", "user.name", "Test"],
        ["git", "add", "package.json"],
        ["git", "commit", "-qm", "initial version"],
    ):
        subprocess.run(command, cwd=project, check=True)

    (project / "package.json").write_text('{"name":"lmstats","version":"0.3.0"}\n')
    fake_npm = fake_bin / "npm"
    fake_npm.write_text(
        "#!/usr/bin/env node\nconsole.error('npm error code E404');\nprocess.exit(1);\n"
    )
    fake_npm.chmod(0o755)
    environment = os.environ | {"PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}"}

    result = subprocess.run(
        ["node", "scripts/should-publish.mjs", "HEAD"],
        cwd=project,
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == "publish=true\n"
