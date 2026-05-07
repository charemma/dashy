"""Tests for the weather module."""

from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx

from dashy.models import Weather
from dashy.weather import get_weather


def _wttr_payload(**overrides: Any) -> dict[str, Any]:
    current: dict[str, Any] = {
        "temp_C": "18",
        "weatherDesc": [{"value": "Partly cloudy"}],
        "windspeedKmph": "12",
        "winddir16Point": "NNW",
        "humidity": "63",
    }
    current.update(overrides)
    return {"current_condition": [current]}


@respx.mock
def test_weather_success_parses_correctly() -> None:
    respx.get("https://wttr.in/Athens").mock(
        return_value=httpx.Response(200, json=_wttr_payload()),
    )

    result = get_weather("Athens")

    assert result == Weather(
        temperature_c=18,
        condition="Partly cloudy",
        wind_speed_kmh=12,
        wind_direction="NNW",
        humidity_percent=63,
    )


@respx.mock
def test_weather_sends_user_agent_header() -> None:
    route = respx.get("https://wttr.in/Athens").mock(
        return_value=httpx.Response(200, json=_wttr_payload()),
    )

    get_weather("Athens")

    assert route.called
    sent_user_agent = route.calls.last.request.headers.get("User-Agent", "")
    assert sent_user_agent.startswith("dashy/")


@respx.mock
def test_weather_handles_http_404() -> None:
    respx.get("https://wttr.in/Atlantis").mock(return_value=httpx.Response(404))

    assert get_weather("Atlantis") is None


@respx.mock
def test_weather_handles_http_500() -> None:
    respx.get("https://wttr.in/Berlin").mock(return_value=httpx.Response(500))

    assert get_weather("Berlin") is None


@respx.mock
def test_weather_handles_connection_timeout() -> None:
    respx.get("https://wttr.in/Athens").mock(side_effect=httpx.ConnectTimeout("timeout"))

    assert get_weather("Athens") is None


@respx.mock
def test_weather_handles_network_error() -> None:
    respx.get("https://wttr.in/Athens").mock(side_effect=httpx.ConnectError("dns failure"))

    assert get_weather("Athens") is None


@respx.mock
def test_weather_handles_invalid_json() -> None:
    respx.get("https://wttr.in/Athens").mock(
        return_value=httpx.Response(200, content=b"not json at all"),
    )

    assert get_weather("Athens") is None


@respx.mock
def test_weather_handles_missing_current_condition() -> None:
    respx.get("https://wttr.in/Athens").mock(
        return_value=httpx.Response(200, json={"weather": []}),
    )

    assert get_weather("Athens") is None


@respx.mock
def test_weather_handles_empty_current_condition() -> None:
    respx.get("https://wttr.in/Athens").mock(
        return_value=httpx.Response(200, json={"current_condition": []}),
    )

    assert get_weather("Athens") is None


@respx.mock
def test_weather_handles_missing_nested_field() -> None:
    payload = _wttr_payload()
    del payload["current_condition"][0]["weatherDesc"]
    respx.get("https://wttr.in/Athens").mock(return_value=httpx.Response(200, json=payload))

    assert get_weather("Athens") is None


@respx.mock
def test_weather_handles_non_numeric_temperature() -> None:
    respx.get("https://wttr.in/Athens").mock(
        return_value=httpx.Response(200, json=_wttr_payload(temp_C="hot")),
    )

    assert get_weather("Athens") is None


@pytest.mark.parametrize("city", ["", "   ", "\t\n"])
def test_weather_rejects_blank_city(city: str) -> None:
    assert get_weather(city) is None


@respx.mock
def test_weather_handles_special_characters_in_city() -> None:
    # httpx URL-encodes the path segment; respx matches on the encoded form.
    route = respx.get("https://wttr.in/S%C3%A3o%20Paulo").mock(
        return_value=httpx.Response(200, json=_wttr_payload()),
    )

    result = get_weather("São Paulo")

    assert route.called
    assert result is not None
    assert result.condition == "Partly cloudy"


def test_weather_model_is_frozen() -> None:
    weather = Weather(
        temperature_c=18,
        condition="Partly cloudy",
        wind_speed_kmh=12,
        wind_direction="NNW",
        humidity_percent=63,
    )
    with pytest.raises(AttributeError):
        weather.temperature_c = 99  # type: ignore[misc]
