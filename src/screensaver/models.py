"""Domain models for weather conditions and rendered output."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import List


@dataclass(slots=True)
class CurrentConditions:
    temperature_c: int
    feels_like_c: int
    humidity: int
    summary: str
    icon: str
    wind_kph: int
    wind_direction: str
    pressure_hpa: int
    observation_time: datetime
    chance_of_rain: int
    cloud_cover: int


@dataclass(slots=True)
class DailyForecast:
    date: date
    min_c: int
    max_c: int
    summary: str
    icon: str
    chance_of_rain: int
    sunrise: time
    sunset: time
    periods: List["PeriodForecast"]


@dataclass(slots=True)
class PeriodForecast:
    label: str
    temp_c: int
    summary: str
    icon: str


@dataclass(slots=True)
class WeatherSnapshot:
    location_name: str
    generated_at: datetime
    current: CurrentConditions
    forecast: List[DailyForecast]
