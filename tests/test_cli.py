"""Tests for the installable LM Stats Viewer command."""

from pathlib import Path
import subprocess
import tomllib

import pytest

from lmstats import cli


def test_version_flag_prints_version_and_exits(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--version"])
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "lmstats" in out


def test_short_version_flag_prints_version_and_exits(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["-v"])
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "lmstats" in out


def test_update_command_runs_npm_install_when_npm_available(monkeypatch, capsys):
    run_calls = []

    class Success:
        returncode = 0

    def fake_run(cmd, **_kwargs):
        run_calls.append(cmd)
        return Success()

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(cli.shutil, "which", lambda name: "/usr/bin/npm" if name == "npm" else None)

    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--update"])

    assert exc_info.value.code == 0
    assert run_calls == [["/usr/bin/npm", "install", "-g", "lmstats"]]
    assert "Update complete" in capsys.readouterr().out


def test_update_command_exits_when_npm_is_missing(monkeypatch, capsys):
    monkeypatch.setattr(cli.shutil, "which", lambda _name: None)

    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--update"])

    assert exc_info.value.code == 1
    assert "npm was not found" in capsys.readouterr().err


def test_update_command_exits_nonzero_on_npm_failure(monkeypatch):
    class Failure:
        returncode = 1

    monkeypatch.setattr(subprocess, "run", lambda _cmd, **_kwargs: Failure())
    monkeypatch.setattr(cli.shutil, "which", lambda name: "/usr/bin/npm" if name == "npm" else None)

    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--update"])

    assert exc_info.value.code == 1


def test_main_creates_configured_application_and_runs_uvicorn(monkeypatch, tmp_path):
    created = []
    run_calls = []
    expected_app = object()
    database_path = str(tmp_path / "history.db")

    def fake_create_app(**kwargs):
        created.append(kwargs)
        return expected_app

    def fake_run(app, **kwargs):
        run_calls.append((app, kwargs))

    monkeypatch.setattr(cli, "create_app", fake_create_app)
    monkeypatch.setattr(cli.uvicorn, "run", fake_run)

    cli.main(["--host", "0.0.0.0", "--port", "9876", "--db", database_path])

    assert created[0]["db_path_resolver"]() == database_path
    assert run_calls == [(
        expected_app,
        {"host": "0.0.0.0", "port": 9876, "log_level": "warning", "timeout_graceful_shutdown": 5},
    )]


def test_package_metadata_keeps_compatibility_modules():
    with (Path(__file__).resolve().parents[1] / "pyproject.toml").open("rb") as config_file:
        config = tomllib.load(config_file)

    assert config["tool"]["setuptools"]["py-modules"] == ["app", "db"]
