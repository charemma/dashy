"""Shared HTTP client factory for dashy data-source modules."""

from __future__ import annotations

from typing import Final

import httpx

from dashy import __version__

_DEFAULT_TIMEOUT_SECONDS: Final = 5.0
_USER_AGENT: Final = f"dashy/{__version__}"


def create_http_client() -> httpx.Client:
    """Create a configured httpx client with timeouts and a User-Agent.

    All dashy data-source modules go through this factory so timeout,
    redirect, and User-Agent behaviour stays consistent. Use it as a
    short-lived context manager and let it close itself:

        with create_http_client() as client:
            response = client.get(url)
    """
    return httpx.Client(
        timeout=_DEFAULT_TIMEOUT_SECONDS,
        follow_redirects=True,
        headers={"User-Agent": _USER_AGENT},
    )
