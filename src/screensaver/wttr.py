"""Client for wttr.in weather data."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time
import json
import logging
from pathlib import Path
from typing import Any

import requests
from dateutil import parser as date_parser
from .config import AppConfig
from .models import CurrentConditions, DailyForecast, PeriodForecast, WeatherSnapshot
from .icons import icon_name_for_code

LOGGER = logging.getLogger(__name__)

PERIOD_DEFINITIONS: list[tuple[str, int]] = [
    ("Morning", 900),
    ("Noon", 1500),
    ("Evening", 2100),
    ("Night", 300),
]


@dataclass(slots=True)
class WttrClient:
    config: AppConfig
    _cache_file: Path = field(init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_cache_file", self.config.cache_dir / "wttr.json")

    def fetch(self, *, use_cache_only: bool = False) -> WeatherSnapshot:
        """Fetch wttr.in JSON and normalize into domain models."""
        payload = self._download_payload(use_cache_only=use_cache_only)
        return self._parse_payload(payload)

    def _download_payload(self, *, use_cache_only: bool) -> dict[str, Any]:
        if use_cache_only:
            if self._cache_file.exists():
                return json.loads(self._cache_file.read_text(encoding="utf-8"))
            raise RuntimeError("Offline mode requested but no cached wttr payload")
        url = (
            f"{self.config.wttr_base_url.rstrip('/')}/"
            f"{self.config.latitude},{self.config.longitude}?format=j1"
        )
        try:
            LOGGER.info("Fetching wttr.in data from %s", url)
            response = requests.get(
                url,
                headers={"User-Agent": "k3w-screensaver/0.1"},
                timeout=15,
            )
            response.raise_for_status()
            self._cache_file.write_text(response.text, encoding="utf-8")
            return response.json()
        except (requests.RequestException, ValueError) as err:
            LOGGER.warning("wttr.in fetch failed: %s", err)
            if self._cache_file.exists():
                LOGGER.info("Falling back to cached wttr payload at %s", self._cache_file)
                return json.loads(self._cache_file.read_text(encoding="utf-8"))
            raise RuntimeError("Unable to fetch wttr data and no cache available") from err

    def _parse_payload(self, payload: dict[str, Any]) -> WeatherSnapshot:
        current_raw = payload["current_condition"][0]
        weather_days = payload["weather"][:3]
        generated_at = datetime.utcnow()
        current = CurrentConditions(
            temperature_c=int(current_raw["temp_C"]),
            feels_like_c=int(current_raw["FeelsLikeC"]),
            humidity=int(current_raw["humidity"]),
            summary=_first_value(current_raw.get("weatherDesc")),
            icon=icon_name_for_code(_safe_int(current_raw.get("weatherCode"))),
            wind_kph=int(current_raw["windspeedKmph"]),
            wind_direction=current_raw["winddir16Point"],
            pressure_hpa=int(current_raw["pressure"]),
            observation_time=_parse_local_datetime(current_raw["localObsDateTime"]),
            chance_of_rain=_extract_hourly_int(weather_days, "chanceofrain"),
            cloud_cover=int(current_raw["cloudcover"]),
        )
        forecast: list[DailyForecast] = []
        for day in weather_days:
            hourly = day.get("hourly", [])
            sunrise, sunset = _parse_astronomy(day.get("astronomy", [{}])[0])
            representative = _representative_hour(hourly)
            periods = [
                _build_period_forecast(label, hourly, target)
                for label, target in PERIOD_DEFINITIONS
            ]
            forecast.append(
                DailyForecast(
                    date=date_parser.parse(day["date"]).date(),
                    min_c=int(day["mintempC"]),
                    max_c=int(day["maxtempC"]),
                    summary=_first_value(representative.get("weatherDesc")),
                    icon=icon_name_for_code(
                        _safe_int(representative.get("weatherCode")),
                    ),
                    chance_of_rain=_max_hourly(hourly, "chanceofrain"),
                    sunrise=sunrise,
                    sunset=sunset,
                    periods=periods,
                )
            )
        return WeatherSnapshot(
            location_name=self.config.location_name,
            generated_at=generated_at,
            current=current,
            forecast=forecast,
        )


def _parse_local_datetime(value: str) -> datetime:
    return date_parser.parse(value)


def _first_value(values: Any, default: str = "") -> str:
    if isinstance(values, list) and values:
        candidate = values[0]
        if isinstance(candidate, dict) and "value" in candidate:
            return candidate["value"].strip()
        if isinstance(candidate, str):
            return candidate.strip()
    if isinstance(values, dict) and "value" in values:
        return str(values["value"]).strip()
    return default


def _max_hourly(hourly: list[dict[str, Any]], key: str) -> int:
    values: list[int] = []
    for hour in hourly:
        try:
            values.append(int(hour.get(key, "0")))
        except (TypeError, ValueError):
            continue
    return max(values) if values else 0


def _extract_hourly_int(weather_days: list[dict[str, Any]], key: str) -> int:
    if not weather_days:
        return 0
    today = weather_days[0]
    return _max_hourly(today.get("hourly", []), key)


def _parse_astronomy(entry: dict[str, Any]) -> tuple[time, time]:
    sunrise = date_parser.parse(entry.get("sunrise", "06:00 AM")).time()
    sunset = date_parser.parse(entry.get("sunset", "06:00 PM")).time()
    return sunrise, sunset


def _representative_hour(hourly: list[dict[str, Any]]) -> dict[str, Any]:
    if not hourly:
        return {}
    best = hourly[0]
    best_delta = float("inf")
    for entry in hourly:
        try:
            time_value = int(str(entry.get("time", "0")))
        except (TypeError, ValueError):
            continue
        delta = abs(time_value - 1200)
        if delta < best_delta:
            best = entry
            best_delta = delta
    return best


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def _build_period_forecast(label: str, hourly: list[dict[str, Any]], target: int) -> PeriodForecast:
    entry = _closest_hour(hourly, target)
    return PeriodForecast(
        label=label,
        temp_c=int(entry.get("tempC", 0)),
        summary=_first_value(entry.get("weatherDesc")),
        icon=icon_name_for_code(_safe_int(entry.get("weatherCode"))),
    )


def _closest_hour(hourly: list[dict[str, Any]], target: int) -> dict[str, Any]:
    if not hourly:
        return {}
    best = hourly[0]
    best_delta = float("inf")
    for entry in hourly:
        value = _safe_int(entry.get("time"), default=0)
        delta = abs(value - target)
        if delta < best_delta:
            best = entry
            best_delta = delta
    return best
