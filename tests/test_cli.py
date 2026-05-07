"""Tests for the dashy CLI dashboard."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest
from click.testing import CliRunner
from rich.console import Console

from dashy import __version__, cli
from dashy.cli import (
    DashboardData,
    fetch_dashboard_data,
    main,
    render_dashboard,
)
from dashy.models import IPInfo, Weather

_FIXED_NOW = datetime(2026, 5, 7, 8, 30, 0)


def _ip() -> IPInfo:
    return IPInfo(ip="203.0.113.42", city="Athens", region="Attica", country="GR")


def _weather() -> Weather:
    return Weather(
        temperature_c=19,
        condition="Light rain",
        wind_speed_kmh=9,
        wind_direction="SSE",
        humidity_percent=100,
    )


def _headlines() -> list[str]:
    return [
        "EU agrees on new AI regulation",
        "Champions League results",
        "Greek economy grows 2.3%",
    ]


def _render_to_string(data: DashboardData) -> str:
    """Render a dashboard into a recorded string for assertions."""
    console = Console(record=True, width=120, force_terminal=False)
    render_dashboard(data, console)
    return console.export_text()


def test_cli_help_includes_description() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "morning briefing" in result.output


def test_cli_version_flag() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.output


def test_cli_runs_end_to_end_with_mocked_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI wires the modules together without crashing."""

    def fake_get_ip_info() -> IPInfo:
        return _ip()

    def fake_get_weather(city: str) -> Weather:
        assert city == "Athens"
        return _weather()

    def fake_get_headlines(feed_url: str | None = None) -> list[str]:
        return _headlines()

    monkeypatch.setattr(cli, "get_ip_info", fake_get_ip_info)
    monkeypatch.setattr(cli, "get_weather", fake_get_weather)
    monkeypatch.setattr(cli, "get_headlines", fake_get_headlines)

    runner = CliRunner()
    result = runner.invoke(main, [])

    assert result.exit_code == 0, result.output
    assert "Athens" in result.output
    assert "Light rain" in result.output
    assert "EU agrees on new AI regulation" in result.output


def test_dashboard_displays_all_data() -> None:
    data = DashboardData(
        ip_info=_ip(),
        weather=_weather(),
        headlines=_headlines(),
        timestamp=_FIXED_NOW,
    )

    output = _render_to_string(data)

    assert "Athens, GR" in output
    assert "203.0.113.42" in output
    assert "19" in output
    assert "Light rain" in output
    assert "9 km/h SSE" in output
    assert "Humidity 100%" in output
    assert "1. EU agrees on new AI regulation" in output
    assert "2. Champions League results" in output
    assert "3. Greek economy grows 2.3%" in output
    assert "07 May 2026" in output


def test_dashboard_handles_ip_failure() -> None:
    data = DashboardData(
        ip_info=None,
        weather=None,
        headlines=_headlines(),
        timestamp=_FIXED_NOW,
    )

    output = _render_to_string(data)

    assert "unavailable" in output
    assert "1. EU agrees on new AI regulation" in output


def test_dashboard_handles_weather_failure() -> None:
    data = DashboardData(
        ip_info=_ip(),
        weather=None,
        headlines=_headlines(),
        timestamp=_FIXED_NOW,
    )

    output = _render_to_string(data)

    assert "Athens, GR" in output
    assert "unavailable" in output
    assert "1. EU agrees on new AI regulation" in output


def test_dashboard_handles_headlines_failure() -> None:
    data = DashboardData(
        ip_info=_ip(),
        weather=_weather(),
        headlines=[],
        timestamp=_FIXED_NOW,
    )

    output = _render_to_string(data)

    assert "Athens, GR" in output
    assert "Light rain" in output
    assert "No headlines available" in output


def test_dashboard_handles_total_failure() -> None:
    data = DashboardData(
        ip_info=None,
        weather=None,
        headlines=[],
        timestamp=_FIXED_NOW,
    )

    output = _render_to_string(data)

    assert "unavailable" in output
    assert "No headlines available" in output
    assert "07 May 2026" in output


def test_dashboard_shows_current_date() -> None:
    timestamp = datetime(2026, 12, 24, 9, 0, 0)
    data = DashboardData(
        ip_info=_ip(),
        weather=_weather(),
        headlines=_headlines(),
        timestamp=timestamp,
    )

    output = _render_to_string(data)

    assert "24 Dec 2026" in output


def test_fetch_dashboard_data_skips_weather_when_ip_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If IP lookup fails, weather is not fetched (no city to query)."""
    weather_called = False

    def fake_get_ip_info() -> IPInfo | None:
        return None

    def fake_get_weather(city: str) -> Weather | None:
        nonlocal weather_called
        weather_called = True
        return None

    def fake_get_headlines(feed_url: str | None = None) -> list[str]:
        return []

    monkeypatch.setattr(cli, "get_ip_info", fake_get_ip_info)
    monkeypatch.setattr(cli, "get_weather", fake_get_weather)
    monkeypatch.setattr(cli, "get_headlines", fake_get_headlines)

    data = fetch_dashboard_data()

    assert data.ip_info is None
    assert data.weather is None
    assert data.headlines == []
    assert weather_called is False


def test_fetch_dashboard_data_uses_ip_city_for_weather(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received_cities: list[str] = []

    def fake_get_ip_info() -> IPInfo:
        return _ip()

    def fake_get_weather(city: str) -> Weather:
        received_cities.append(city)
        return _weather()

    def fake_get_headlines(feed_url: str | None = None) -> list[str]:
        return _headlines()

    monkeypatch.setattr(cli, "get_ip_info", fake_get_ip_info)
    monkeypatch.setattr(cli, "get_weather", fake_get_weather)
    monkeypatch.setattr(cli, "get_headlines", fake_get_headlines)

    data = fetch_dashboard_data()

    assert received_cities == ["Athens"]
    assert data.ip_info == _ip()
    assert data.weather == _weather()
    assert data.headlines == _headlines()


def test_cli_does_not_crash_when_all_sources_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get_ip_info() -> IPInfo | None:
        return None

    def fake_get_weather(city: str) -> Weather | None:
        return None

    def fake_get_headlines(feed_url: str | None = None) -> list[str]:
        return []

    monkeypatch.setattr(cli, "get_ip_info", fake_get_ip_info)
    monkeypatch.setattr(cli, "get_weather", fake_get_weather)
    monkeypatch.setattr(cli, "get_headlines", fake_get_headlines)

    runner = CliRunner()
    result = runner.invoke(main, [])

    assert result.exit_code == 0, result.output
    assert "unavailable" in result.output
    assert "No headlines available" in result.output


def test_dashboard_caps_at_module_max_headlines() -> None:
    """Five headlines (the news module's max) are all rendered and numbered."""
    data = DashboardData(
        ip_info=_ip(),
        weather=_weather(),
        headlines=[f"Headline {i}" for i in range(1, 6)],
        timestamp=_FIXED_NOW,
    )

    output = _render_to_string(data)

    for i in range(1, 6):
        assert f"{i}. Headline {i}" in output


def test_render_dashboard_returns_none() -> None:
    """Render side-effects only; the function returns None."""
    data = DashboardData(
        ip_info=_ip(),
        weather=_weather(),
        headlines=_headlines(),
        timestamp=_FIXED_NOW,
    )
    console = Console(record=True, width=120, force_terminal=False)

    result: Any = render_dashboard(data, console)

    assert result is None
