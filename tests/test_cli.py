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
_BOX_CHARS = "\u256d\u2500\u256e\u2502\u2570\u256f\u2571\u2572\u2573"


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
    assert "Attica" in output
    assert "203.0.113.42" in output
    assert "19" in output
    assert "Light rain" in output
    assert "9 km/h SSE" in output
    assert "100% humidity" in output
    assert "  1  EU agrees on new AI regulation" in output
    assert "  2  Champions League results" in output
    assert "  3  Greek economy grows 2.3%" in output
    assert "07 May 2026 08:30" in output


def test_dashboard_handles_ip_failure() -> None:
    data = DashboardData(
        ip_info=None,
        weather=None,
        headlines=_headlines(),
        timestamp=_FIXED_NOW,
    )

    output = _render_to_string(data)

    assert "Unknown location" in output
    assert "Weather unavailable" in output
    assert "  1  EU agrees on new AI regulation" in output


def test_dashboard_handles_weather_failure() -> None:
    data = DashboardData(
        ip_info=_ip(),
        weather=None,
        headlines=_headlines(),
        timestamp=_FIXED_NOW,
    )

    output = _render_to_string(data)

    assert "Athens, GR" in output
    assert "Weather unavailable" in output
    assert "  1  EU agrees on new AI regulation" in output


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

    assert "Unknown location" in output
    assert "Weather unavailable" in output
    assert "No headlines available" in output
    assert "07 May 2026 08:30" in output


def test_dashboard_shows_current_date_and_time() -> None:
    timestamp = datetime(2026, 12, 24, 9, 0, 0)
    data = DashboardData(
        ip_info=_ip(),
        weather=_weather(),
        headlines=_headlines(),
        timestamp=timestamp,
    )

    output = _render_to_string(data)

    assert "24 Dec 2026" in output
    assert "09:00" in output
    assert "24 Dec 2026 09:00" in output


def test_dashboard_renders_time_with_evening_timestamp() -> None:
    """Late timestamps render as zero-padded 24h time."""
    timestamp = datetime(2026, 5, 7, 23, 5, 0)
    data = DashboardData(
        ip_info=_ip(),
        weather=_weather(),
        headlines=_headlines(),
        timestamp=timestamp,
    )

    output = _render_to_string(data)

    assert "07 May 2026 23:05" in output


def test_fetch_dashboard_data_falls_back_to_default_city_when_ip_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If IP lookup fails, weather is still fetched using the default city."""
    monkeypatch.delenv("DASHY_DEFAULT_CITY", raising=False)
    received_cities: list[str] = []

    def fake_get_ip_info() -> IPInfo | None:
        return None

    def fake_get_weather(city: str) -> Weather | None:
        received_cities.append(city)
        return _weather()

    def fake_get_headlines(feed_url: str | None = None) -> list[str]:
        return _headlines()

    monkeypatch.setattr(cli, "get_ip_info", fake_get_ip_info)
    monkeypatch.setattr(cli, "get_weather", fake_get_weather)
    monkeypatch.setattr(cli, "get_headlines", fake_get_headlines)

    data = fetch_dashboard_data()

    assert data.ip_info is None
    assert received_cities == ["Athens"]
    assert data.weather == _weather()
    assert data.headlines == _headlines()


def test_fetch_dashboard_data_default_city_overridable_via_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``DASHY_DEFAULT_CITY`` overrides the built-in fallback city."""
    monkeypatch.setenv("DASHY_DEFAULT_CITY", "Berlin")
    received_cities: list[str] = []

    def fake_get_ip_info() -> IPInfo | None:
        return None

    def fake_get_weather(city: str) -> Weather | None:
        received_cities.append(city)
        return None

    def fake_get_headlines(feed_url: str | None = None) -> list[str]:
        return []

    monkeypatch.setattr(cli, "get_ip_info", fake_get_ip_info)
    monkeypatch.setattr(cli, "get_weather", fake_get_weather)
    monkeypatch.setattr(cli, "get_headlines", fake_get_headlines)

    fetch_dashboard_data()

    assert received_cities == ["Berlin"]


def test_fetch_dashboard_data_weather_failure_does_not_suppress_other_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When weather fallback returns None, IP and headlines still display."""
    monkeypatch.delenv("DASHY_DEFAULT_CITY", raising=False)

    def fake_get_ip_info() -> IPInfo | None:
        return None

    def fake_get_weather(city: str) -> Weather | None:
        return None

    def fake_get_headlines(feed_url: str | None = None) -> list[str]:
        return _headlines()

    monkeypatch.setattr(cli, "get_ip_info", fake_get_ip_info)
    monkeypatch.setattr(cli, "get_weather", fake_get_weather)
    monkeypatch.setattr(cli, "get_headlines", fake_get_headlines)

    data = fetch_dashboard_data()

    assert data.ip_info is None
    assert data.weather is None
    assert data.headlines == _headlines()


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
    assert "Unknown location" in result.output
    assert "Weather unavailable" in result.output
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
        assert f"  {i}  Headline {i}" in output


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


# --- New tests for the redesigned UI -----------------------------------


@pytest.mark.parametrize(
    "condition, expected",
    [
        ("Clear sky", "\u2600\ufe0f"),
        ("Sunny", "\u2600\ufe0f"),
        ("Partly cloudy", "\u26c5"),
        ("Scattered clouds", "\u26c5"),
        ("Light rain", "\U0001f327\ufe0f"),
        ("Drizzle", "\U0001f327\ufe0f"),
        ("Heavy snow", "\u2744\ufe0f"),
        ("Thunderstorm", "\u26c8\ufe0f"),
        ("Storm warning", "\u26c8\ufe0f"),
        ("Fog", "\U0001f32b\ufe0f"),
        ("Mist", "\U0001f32b\ufe0f"),
        ("Cloudy", "\u2601\ufe0f"),
        ("Overcast", "\u2601\ufe0f"),
        ("", "\U0001f321\ufe0f"),
        ("Tornado", "\U0001f321\ufe0f"),
    ],
)
def test_weather_icon_mapping(condition: str, expected: str) -> None:
    """``_weather_icon`` maps known condition keywords to Unicode icons."""
    assert cli._weather_icon(condition) == expected


def test_weather_icon_is_case_insensitive() -> None:
    assert cli._weather_icon("PARTLY CLOUDY") == "\u26c5"
    assert cli._weather_icon("Light Rain") == "\U0001f327\ufe0f"


def test_weather_icon_picks_specific_match_first() -> None:
    """A 'partly cloudy' string matches the partly-cloudy icon, not the
    bare cloud icon -- specific matches win.
    """
    assert cli._weather_icon("Partly cloudy") == "\u26c5"


def test_header_format_has_no_morning_briefing_text() -> None:
    timestamp = datetime(2026, 5, 7, 12, 35, 0)
    data = DashboardData(
        ip_info=_ip(),
        weather=_weather(),
        headlines=_headlines(),
        timestamp=timestamp,
    )

    output = _render_to_string(data)

    assert "morning briefing" not in output
    assert "dashy  \u00b7  07 May 2026 12:35" in output


def test_dashboard_has_no_panel_borders() -> None:
    """No box-drawing characters should appear -- the redesign is panel-free."""
    data = DashboardData(
        ip_info=_ip(),
        weather=_weather(),
        headlines=_headlines(),
        timestamp=_FIXED_NOW,
    )

    output = _render_to_string(data)

    for char in _BOX_CHARS:
        assert char not in output, f"Unexpected box-drawing character {char!r} in output"


def test_dashboard_renders_weather_icon_in_output() -> None:
    data = DashboardData(
        ip_info=_ip(),
        weather=_weather(),
        headlines=_headlines(),
        timestamp=_FIXED_NOW,
    )

    output = _render_to_string(data)

    assert "\U0001f327\ufe0f" in output  # rain icon for "Light rain"


def test_location_and_weather_share_first_line() -> None:
    """City and the weather summary must end up on the same row."""
    data = DashboardData(
        ip_info=_ip(),
        weather=_weather(),
        headlines=_headlines(),
        timestamp=_FIXED_NOW,
    )

    output = _render_to_string(data)
    lines = output.splitlines()

    matching = [line for line in lines if "Athens, GR" in line]
    assert matching, "Expected a line containing the city"
    first = matching[0]
    assert "Light rain" in first, f"Weather should share the city line: {first!r}"
    assert "19\u00b0C" in first


def test_region_skipped_when_equal_to_city() -> None:
    ip = IPInfo(ip="198.51.100.7", city="Berlin", region="Berlin", country="DE")
    data = DashboardData(
        ip_info=ip,
        weather=_weather(),
        headlines=_headlines(),
        timestamp=_FIXED_NOW,
    )

    output = _render_to_string(data)
    lines = [line for line in output.splitlines() if line.strip() == "Berlin"]
    assert lines == []


def test_headlines_use_two_space_indent() -> None:
    data = DashboardData(
        ip_info=_ip(),
        weather=_weather(),
        headlines=_headlines(),
        timestamp=_FIXED_NOW,
    )

    output = _render_to_string(data)
    lines = output.splitlines()

    assert "Headlines" in [line.strip() for line in lines]
    assert any(line.startswith("  1  EU agrees on new AI regulation") for line in lines)
