"""Weather module: fetches current weather from wttr.in."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

import httpx

_WTTR_URL: Final = "https://wttr.in/{city}"
_REQUEST_TIMEOUT_SECONDS: Final = 5.0
_UNKNOWN: Final = "unknown"


@dataclass(frozen=True)
class WeatherData:
    """Structured weather data for a single location."""

    temperature_c: int
    condition: str
    wind_kmph: int
    wind_direction: str
    humidity: int

    @classmethod
    def unavailable(cls) -> WeatherData:
        """Fallback value when weather cannot be fetched or parsed."""
        return cls(
            temperature_c=0,
            condition=_UNKNOWN,
            wind_kmph=0,
            wind_direction=_UNKNOWN,
            humidity=0,
        )


def get_weather(city: str) -> WeatherData:
    """Fetch current weather for the given city.

    Returns ``WeatherData`` with current conditions on success, or
    ``WeatherData.unavailable()`` on any error. Never raises.
    """
    if not city or not city.strip():
        return WeatherData.unavailable()

    try:
        response = httpx.get(
            _WTTR_URL.format(city=city.strip()),
            params={"format": "j1"},
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError):
        return WeatherData.unavailable()

    return _parse_payload(payload)


def _parse_payload(payload: Any) -> WeatherData:
    """Parse the wttr.in JSON payload into ``WeatherData``.

    Returns ``WeatherData.unavailable()`` if any required field is missing
    or has an unexpected type.
    """
    try:
        current = payload["current_condition"][0]
        return WeatherData(
            temperature_c=int(current["temp_C"]),
            condition=str(current["weatherDesc"][0]["value"]),
            wind_kmph=int(current["windspeedKmph"]),
            wind_direction=str(current["winddir16Point"]),
            humidity=int(current["humidity"]),
        )
    except (KeyError, IndexError, TypeError, ValueError):
        return WeatherData.unavailable()
