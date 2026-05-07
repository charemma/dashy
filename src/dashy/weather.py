"""Weather module: fetches current weather from wttr.in."""

from __future__ import annotations

from typing import Any, Final

import httpx

from dashy.http import create_http_client
from dashy.models import Weather

_WTTR_URL: Final = "https://wttr.in/{city}"


def get_weather(city: str) -> Weather | None:
    """Fetch current weather for the given city.

    Returns a ``Weather`` object on success or ``None`` on any error
    (network failure, non-2xx response, malformed payload, missing
    fields, blank city). Never raises.
    """
    if not city or not city.strip():
        return None

    with create_http_client() as client:
        try:
            response = client.get(
                _WTTR_URL.format(city=city.strip()),
                params={"format": "j1"},
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            return None

    return _parse_payload(payload)


def _parse_payload(payload: Any) -> Weather | None:
    """Parse the wttr.in JSON payload into ``Weather``.

    Returns ``None`` if any required field is missing or has an
    unexpected type.
    """
    try:
        current = payload["current_condition"][0]
        return Weather(
            temperature_c=int(current["temp_C"]),
            condition=str(current["weatherDesc"][0]["value"]),
            wind_speed_kmh=int(current["windspeedKmph"]),
            wind_direction=str(current["winddir16Point"]),
            humidity_percent=int(current["humidity"]),
        )
    except (KeyError, IndexError, TypeError, ValueError):
        return None
