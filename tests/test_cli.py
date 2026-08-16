"""Tests for the installable LM Speed Viewer command."""

from pathlib import Path
import tomllib

from lm_speed_viewer import cli


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
