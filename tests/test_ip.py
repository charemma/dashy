"""Tests for the ip module."""

from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx

from dashy.ip import get_ip_info
from dashy.models import IPInfo

_IPINFO_URL = "https://ipinfo.io/json"


def _ipinfo_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ip": "203.0.113.42",
        "city": "Athens",
        "region": "Attica",
        "country": "GR",
    }
    payload.update(overrides)
    return payload


@respx.mock
def test_ip_success_parses_correctly() -> None:
    respx.get(_IPINFO_URL).mock(
        return_value=httpx.Response(200, json=_ipinfo_payload()),
    )

    result = get_ip_info()

    assert result == IPInfo(
        ip="203.0.113.42",
        city="Athens",
        region="Attica",
        country="GR",
    )


@respx.mock
def test_ip_sends_user_agent_header() -> None:
    route = respx.get(_IPINFO_URL).mock(
        return_value=httpx.Response(200, json=_ipinfo_payload()),
    )

    get_ip_info()

    assert route.called
    sent_user_agent = route.calls.last.request.headers.get("User-Agent", "")
    assert sent_user_agent.startswith("dashy/")


@respx.mock
def test_ip_handles_http_404() -> None:
    respx.get(_IPINFO_URL).mock(return_value=httpx.Response(404))

    assert get_ip_info() is None


@respx.mock
def test_ip_handles_http_429() -> None:
    respx.get(_IPINFO_URL).mock(return_value=httpx.Response(429))

    assert get_ip_info() is None


@respx.mock
def test_ip_handles_http_500() -> None:
    respx.get(_IPINFO_URL).mock(return_value=httpx.Response(500))

    assert get_ip_info() is None


@respx.mock
def test_ip_handles_connection_timeout() -> None:
    respx.get(_IPINFO_URL).mock(side_effect=httpx.ConnectTimeout("timeout"))

    assert get_ip_info() is None


@respx.mock
def test_ip_handles_network_error() -> None:
    respx.get(_IPINFO_URL).mock(side_effect=httpx.ConnectError("dns failure"))

    assert get_ip_info() is None


@respx.mock
def test_ip_handles_invalid_json() -> None:
    respx.get(_IPINFO_URL).mock(
        return_value=httpx.Response(200, content=b"not json at all"),
    )

    assert get_ip_info() is None


@pytest.mark.parametrize("missing_field", ["ip", "city", "region", "country"])
@respx.mock
def test_ip_handles_missing_field(missing_field: str) -> None:
    payload = _ipinfo_payload()
    del payload[missing_field]
    respx.get(_IPINFO_URL).mock(return_value=httpx.Response(200, json=payload))

    assert get_ip_info() is None


@pytest.mark.parametrize("nulled_field", ["ip", "city", "region", "country"])
@respx.mock
def test_ip_handles_null_field(nulled_field: str) -> None:
    payload = _ipinfo_payload(**{nulled_field: None})
    respx.get(_IPINFO_URL).mock(return_value=httpx.Response(200, json=payload))

    assert get_ip_info() is None


@respx.mock
def test_ip_handles_non_object_payload() -> None:
    respx.get(_IPINFO_URL).mock(
        return_value=httpx.Response(200, json=["not", "an", "object"]),
    )

    assert get_ip_info() is None


def test_ip_model_is_frozen() -> None:
    info = IPInfo(ip="203.0.113.42", city="Athens", region="Attica", country="GR")
    with pytest.raises(AttributeError):
        info.ip = "10.0.0.1"  # type: ignore[misc]
