"""Command-line entry point for dashy."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime

import click
from rich.columns import Columns
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text

from dashy import __version__
from dashy.ip import get_ip_info
from dashy.models import Headlines, IPInfo, Weather
from dashy.news import get_headlines
from dashy.weather import get_weather

_UNAVAILABLE = "[dim]unavailable[/dim]"
_DATETIME_FORMAT = "%d %b %Y %H:%M"
_PANEL_BORDER_STYLE = "cyan"
_DEFAULT_CITY = "Athens"
_DEFAULT_CITY_ENV = "DASHY_DEFAULT_CITY"


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
    headlines = get_headlines()
    return DashboardData(
        ip_info=ip_info,
        weather=weather,
        headlines=headlines,
        timestamp=datetime.now(),
    )


def _render_header(timestamp: datetime) -> Text:
    """Build the header line: app name on the left, date and time on the right."""
    header = Text()
    header.append("dashy", style="bold cyan")
    header.append("  ")
    header.append("morning briefing", style="dim")
    header.append("    ")
    header.append(timestamp.strftime(_DATETIME_FORMAT), style="bold white")
    return header


def _render_location(ip_info: IPInfo | None) -> Panel:
    """Render the location panel from IP geolocation data."""
    body = Text()
    if ip_info is None:
        body.append("Location: ", style="bold")
        body.append_text(Text.from_markup(_UNAVAILABLE))
        body.append("\n")
        body.append("IP: ", style="bold")
        body.append_text(Text.from_markup(_UNAVAILABLE))
    else:
        body.append(f"{ip_info.city}, {ip_info.country}", style="bold green")
        if ip_info.region and ip_info.region != ip_info.city:
            body.append(f"\n{ip_info.region}", style="green")
        body.append(f"\n{ip_info.ip}", style="white")

    return Panel(
        body,
        title="[bold]Location[/bold]",
        border_style=_PANEL_BORDER_STYLE,
        padding=(1, 2),
        expand=True,
    )


def _render_weather(weather: Weather | None) -> Panel:
    """Render the weather panel from current conditions."""
    body = Text()
    if weather is None:
        body.append("Weather: ", style="bold")
        body.append_text(Text.from_markup(_UNAVAILABLE))
    else:
        body.append(f"{weather.temperature_c}°C", style="bold yellow")
        body.append("  ")
        body.append(weather.condition, style="cyan")
        body.append("\n")
        body.append(
            f"Wind {weather.wind_speed_kmh} km/h {weather.wind_direction}",
            style="white",
        )
        body.append("\n")
        body.append(f"Humidity {weather.humidity_percent}%", style="white")

    return Panel(
        body,
        title="[bold]Weather[/bold]",
        border_style=_PANEL_BORDER_STYLE,
        padding=(1, 2),
        expand=True,
    )


def _render_headlines(headlines: Headlines) -> Panel:
    """Render the headlines panel as a numbered list."""
    body = Text()
    if not headlines:
        body.append("No headlines available", style="dim")
    else:
        for index, headline in enumerate(headlines, start=1):
            if index > 1:
                body.append("\n")
            body.append(f"{index}. ", style="bold cyan")
            body.append(headline, style="white")

    return Panel(
        body,
        title="[bold]Headlines[/bold]",
        border_style=_PANEL_BORDER_STYLE,
        padding=(1, 2),
        expand=True,
    )


def render_dashboard(data: DashboardData, console: Console) -> None:
    """Render the full dashboard to ``console``."""
    header = _render_header(data.timestamp)
    location_panel = _render_location(data.ip_info)
    weather_panel = _render_weather(data.weather)
    headlines_panel = _render_headlines(data.headlines)

    columns = Columns(
        [location_panel, weather_panel],
        equal=True,
        expand=True,
    )

    body = Group(header, Text(""), columns, headlines_panel)
    console.print(Panel(body, border_style=_PANEL_BORDER_STYLE, padding=(1, 2)))


@click.command()
@click.version_option(version=__version__, prog_name="dashy")
def main() -> None:
    """dashy -- your morning briefing in the terminal."""
    console = Console()
    data = fetch_dashboard_data()
    render_dashboard(data, console)


if __name__ == "__main__":
    main()
