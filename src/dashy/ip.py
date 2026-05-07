"""IP module: fetches public IP and geolocation from ipinfo.io."""

from __future__ import annotations

from typing import Any, Final

import httpx

from dashy.http import create_http_client
from dashy.models import IPInfo

_IPINFO_URL: Final = "https://ipinfo.io/json"


def get_ip_info() -> IPInfo | None:
    """Fetch the current public IP and location from ipinfo.io.

    Returns an ``IPInfo`` object on success or ``None`` on any error
    (network failure, non-2xx response, malformed payload, missing
    fields). Never raises.
    """
    with create_http_client() as client:
        try:
            response = client.get(_IPINFO_URL)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            return None

    return _parse_payload(payload)


def _parse_payload(payload: Any) -> IPInfo | None:
    """Parse the ipinfo.io JSON payload into ``IPInfo``.

    Returns ``None`` if any required field is missing or has an
    unexpected type.
    """
    try:
        ip = payload["ip"]
        city = payload["city"]
        region = payload["region"]
        country = payload["country"]
    except (KeyError, TypeError):
        return None

    if not all(isinstance(value, str) for value in (ip, city, region, country)):
        return None

    return IPInfo(ip=ip, city=city, region=region, country=country)
