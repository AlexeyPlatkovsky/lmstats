"""Tests for isolated application factory runtime services."""

from datetime import datetime, timezone

from lmstats import database
from lmstats.application import create_app
from lmstats.collector import Collector


def test_create_app_isolates_runtime_services(tmp_path):
    """Created apps retain independent collector, clock, and database configuration."""
    first_collector = Collector()
    second_collector = Collector()
    def first_clock():
        return datetime(2026, 1, 1, tzinfo=timezone.utc)

    def second_clock():
        return datetime(2026, 2, 1, tzinfo=timezone.utc)
    first_path = str(tmp_path / "first.db")
    second_path = str(tmp_path / "second.db")

    first = create_app(
        collector=first_collector,
        db_path_resolver=lambda: first_path,
        clock=first_clock,
    )
    second = create_app(
        collector=second_collector,
        db_path_resolver=lambda: second_path,
        clock=second_clock,
    )

    assert first.state.collector is first_collector
    assert second.state.collector is second_collector
    assert first.state.collector is not second.state.collector
    assert first.state.clock() == first_clock()
    assert second.state.clock() == second_clock()
    assert first.state.db_path_resolver() == first_path
    assert second.state.db_path_resolver() == second_path


def test_default_database_path_is_resolved_after_factory_creation(monkeypatch, tmp_path):
    """The compatibility app can still patch the default resolver before startup."""
    app = create_app()
    expected = str(tmp_path / "history.db")

    monkeypatch.setattr(database, "default_db_path", lambda: expected)

    assert app.state.db_path_resolver() == expected
