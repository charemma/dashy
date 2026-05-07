"""Tests for the shared HTTP client factory."""

from __future__ import annotations

import httpx
import respx

from dashy import __version__
from dashy.http import create_http_client


def test_create_http_client_returns_client() -> None:
    with create_http_client() as client:
        assert isinstance(client, httpx.Client)


def test_create_http_client_sets_user_agent() -> None:
    with create_http_client() as client:
        assert client.headers["User-Agent"] == f"dashy/{__version__}"


def test_create_http_client_follows_redirects() -> None:
    with create_http_client() as client:
        assert client.follow_redirects is True


def test_create_http_client_has_timeout() -> None:
    with create_http_client() as client:
        # httpx exposes the configured timeout on the client.
        assert client.timeout.connect is not None
        assert client.timeout.read is not None


@respx.mock
def test_create_http_client_sends_user_agent_on_request() -> None:
    route = respx.get("https://example.invalid/ping").mock(
        return_value=httpx.Response(200, text="ok"),
    )

    with create_http_client() as client:
        response = client.get("https://example.invalid/ping")

    assert response.status_code == 200
    assert route.called
    assert route.calls.last.request.headers["User-Agent"] == f"dashy/{__version__}"
