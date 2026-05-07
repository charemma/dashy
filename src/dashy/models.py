"""Shared data models for dashy data-source modules."""

from __future__ import annotations

from dataclasses import dataclass

Headlines = list[str]
"""A list of news headline titles. See ``dashy.news.get_headlines``."""


@dataclass(frozen=True)
class Weather:
    """Current weather conditions for a single location."""

    temperature_c: int
    condition: str
    wind_speed_kmh: int
    wind_direction: str
    humidity_percent: int


@dataclass(frozen=True)
class IPInfo:
    """Public IP address and geolocation data from ipinfo.io."""

    ip: str
    city: str
    region: str
    country: str
