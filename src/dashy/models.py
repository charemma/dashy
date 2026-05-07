"""Shared data models for dashy data-source modules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Weather:
    """Current weather conditions for a single location."""

    temperature_c: int
    condition: str
    wind_speed_kmh: int
    wind_direction: str
    humidity_percent: int
