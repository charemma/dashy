"""Command-line entry point for dashy."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime

import click
from rich.console import Console
from rich.text import Text

from dashy import __version__
from dashy.ip import get_ip_info
from dashy.models import Headlines, IPInfo, Weather
from dashy.news import get_headlines
from dashy.weather import get_weather

_DATETIME_FORMAT = "%d %b %Y %H:%M"
_DEFAULT_CITY = "Athens"
_DEFAULT_CITY_ENV = "DASHY_DEFAULT_CITY"
_DASHBOARD_WIDTH = 78
_UNKNOWN_LOCATION = "Unknown location"
_WEATHER_UNAVAILABLE = "Weather unavailable"


def _resolve_default_city() -> str:
    """Return the fallback weather city.

    Honours the ``DASHY_DEFAULT_CITY`` environment variable so users on
    different machines can override the built-in default without code
    changes.
    """
    override = os.environ.get(_DEFAULT_CITY_ENV, "").strip()
    return override or _DEFAULT_CITY


@dataclass(frozen=True)
class DashboardData:
    """Aggregated data for a single dashboard render."""

    ip_info: IPInfo | None
    weather: Weather | None
    headlines: Headlines
    timestamp: datetime


def fetch_dashboard_data() -> DashboardData:
    """Fetch IP, weather, and headlines for the dashboard.

    Each source is independent: a failure in one does not suppress the
    others. When IP lookup fails, weather falls back to a default city
    (``DASHY_DEFAULT_CITY`` env var, otherwise the built-in default) so
    the user still sees weather data for a sensible location.
    """
    ip_info = get_ip_info()
    city = ip_info.city if ip_info is not None else _resolve_default_city()
    weather = get_weather(city)
    country_code = ip_info.country if ip_info is not None else None
    headlines = get_headlines(country_code)
    return DashboardData(
        ip_info=ip_info,
        weather=weather,
        headlines=headlines,
        timestamp=datetime.now(),
    )


def _weather_icon(condition: str) -> str:
    """Map a weather condition string to a Unicode icon.

    Matching is case-insensitive and uses substring lookups so that
    multi-word conditions like ``"Partly cloudy"`` resolve to the more
    specific icon. Unknown conditions fall back to a generic thermometer.
    """
    condition_lower = condition.lower()
    if "thunder" in condition_lower or "storm" in condition_lower:
        return "\u26c8\ufe0f"  # thunder cloud and rain
    if "partly" in condition_lower or "scattered" in condition_lower:
        return "\u26c5"  # sun behind cloud
    if "clear" in condition_lower or "sunny" in condition_lower:
        return "\u2600\ufe0f"  # sun
    if "rain" in condition_lower or "drizzle" in condition_lower:
        return "\U0001f327\ufe0f"  # cloud with rain
    if "snow" in condition_lower:
        return "\u2744\ufe0f"  # snowflake
    if "fog" in condition_lower or "mist" in condition_lower:
        return "\U0001f32b\ufe0f"  # fog
    if "cloud" in condition_lower or "overcast" in condition_lower:
        return "\u2601\ufe0f"  # cloud
    return "\U0001f321\ufe0f"  # thermometer


def _render_header(timestamp: datetime) -> Text:
    """Build the header line: app name, separator, timestamp."""
    header = Text()
    header.append("dashy", style="dim")
    header.append("  \u00b7  ", style="dim")
    header.append(timestamp.strftime(_DATETIME_FORMAT), style="white")
    return header


def _join_aligned(left: Text, right: Text, width: int) -> Text:
    """Join two ``Text`` blocks on a single line, left- and right-aligned.

    The padding is computed from the rendered character lengths. If the
    combined content exceeds ``width`` the two blocks are stacked on
    separate lines so nothing collides.
    """
    line = Text()
    left_len = len(left.plain)
    right_len = len(right.plain)
    padding = width - left_len - right_len
    if padding < 1:
        line.append_text(left)
        line.append("\n")
        line.append_text(right)
        return line
    line.append_text(left)
    line.append(" " * padding)
    line.append_text(right)
    return line


def _location_left_lines(ip_info: IPInfo | None) -> list[Text]:
    """Build the left column (location) as a list of ``Text`` rows."""
    if ip_info is None:
        return [Text(_UNKNOWN_LOCATION, style="dim")]

    rows: list[Text] = []
    primary = Text()
    primary.append(f"{ip_info.city}, {ip_info.country}", style="bold green")
    rows.append(primary)

    if ip_info.region and ip_info.region != ip_info.city:
        rows.append(Text(ip_info.region, style="dim"))

    rows.append(Text(ip_info.ip, style="dim"))
    return rows


def _weather_right_lines(weather: Weather | None) -> list[Text]:
    """Build the right column (weather) as a list of ``Text`` rows."""
    if weather is None:
        return [Text(_WEATHER_UNAVAILABLE, style="dim")]

    summary = Text()
    summary.append(_weather_icon(weather.condition))
    summary.append("  ")
    summary.append(f"{weather.temperature_c}\u00b0C", style="bold yellow")
    summary.append("  ")
    summary.append(weather.condition, style="white")

    detail = Text()
    detail.append(
        f"{weather.wind_speed_kmh} km/h {weather.wind_direction}",
        style="dim",
    )
    detail.append("  \u00b7  ", style="dim")
    detail.append(f"{weather.humidity_percent}% humidity", style="dim")

    return [summary, detail]


def _render_location_weather(
    ip_info: IPInfo | None,
    weather: Weather | None,
    width: int = _DASHBOARD_WIDTH,
) -> Text:
    """Render the merged location + weather block.

    Location data is drawn on the left, weather on the right, padded to
    ``width`` characters. Rows that only have content on one side render
    with that side alone (no trailing spaces).
    """
    left_rows = _location_left_lines(ip_info)
    right_rows = _weather_right_lines(weather)

    body = Text()
    max_rows = max(len(left_rows), len(right_rows))
    for i in range(max_rows):
        left = left_rows[i] if i < len(left_rows) else Text("")
        right = right_rows[i] if i < len(right_rows) else None
        if right is None:
            body.append_text(left)
        elif not left.plain:
            padding = max(width - len(right.plain), 0)
            body.append(" " * padding)
            body.append_text(right)
        else:
            body.append_text(_join_aligned(left, right, width))
        if i < max_rows - 1:
            body.append("\n")
    return body


def _render_headlines(headlines: Headlines) -> Text:
    """Render the headlines section.

    Plain section header followed by a numbered list. Each item is
    indented with two spaces, then the number (bold cyan), then two
    spaces, then the title.
    """
    body = Text()
    body.append("Headlines", style="bold white")
    body.append("\n\n")

    if not headlines:
        body.append("  No headlines available", style="dim")
        return body

    for index, headline in enumerate(headlines, start=1):
        if index > 1:
            body.append("\n")
        body.append(f"  {index}  ", style="bold cyan")
        body.append(headline, style="white")

    return body


def render_dashboard(data: DashboardData, console: Console) -> None:
    """Render the full dashboard to ``console``.

    Layout: header line, blank line, location/weather block, blank line,
    headlines section. No panels, no borders -- whitespace and alignment
    only.
    """
    console.print(_render_header(data.timestamp))
    console.print()
    console.print(_render_location_weather(data.ip_info, data.weather))
    console.print()
    console.print(_render_headlines(data.headlines))


@click.command()
@click.version_option(version=__version__, prog_name="dashy")
def main() -> None:
    """dashy -- your morning briefing in the terminal."""
    console = Console()
    data = fetch_dashboard_data()
    render_dashboard(data, console)


if __name__ == "__main__":
    main()
