from __future__ import annotations

from datetime import date, datetime, time
from pathlib import Path

from PIL import Image

from screensaver.config import AppConfig, R2Config
from screensaver.models import (
    CurrentConditions,
    DailyForecast,
    PeriodForecast,
    WeatherSnapshot,
)
from screensaver.renderer import Renderer


def _config(tmp_path: Path) -> AppConfig:
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    output = tmp_path / "out"
    output.mkdir()
    return AppConfig(
        latitude=0.0,
        longitude=0.0,
        location_name="Test City",
        image_width=600,
        image_height=800,
        grayscale=True,
        cache_dir=cache_dir,
        output_path=output,
        r2=R2Config(
            enabled=False,
            account_id=None,
            access_key_id=None,
            secret_access_key=None,
            bucket=None,
            key_prefix="",
            endpoint_url=None,
        ),
        wttr_base_url="https://wttr.in",
    )


def _snapshot() -> WeatherSnapshot:
    current = CurrentConditions(
        temperature_c=2,
        feels_like_c=0,
        humidity=70,
        summary="Partly cloudy",
        icon="few",
        wind_kph=12,
        wind_direction="NW",
        pressure_hpa=1020,
        observation_time=datetime(2026, 1, 1, 12, 30),
        chance_of_rain=45,
        cloud_cover=40,
    )
    forecast = [
        DailyForecast(
            date=date(2026, 1, 1),
            min_c=-1,
            max_c=4,
            summary="Cloudy",
            icon="bkn",
            chance_of_rain=40,
            sunrise=time(8, 30),
            sunset=time(17, 48),
            periods=_periods(),
        ),
        DailyForecast(
            date=date(2026, 1, 2),
            min_c=-2,
            max_c=3,
            summary="Snow",
            icon="sn",
            chance_of_rain=60,
            sunrise=time(8, 31),
            sunset=time(17, 49),
            periods=_periods(),
        ),
        DailyForecast(
            date=date(2026, 1, 3),
            min_c=-3,
            max_c=2,
            summary="Clear",
            icon="skc",
            chance_of_rain=10,
            sunrise=time(8, 31),
            sunset=time(17, 50),
            periods=_periods(),
        ),
    ]
    return WeatherSnapshot(
        location_name="Test City",
        generated_at=datetime(2026, 1, 1, 12, 30),
        current=current,
        forecast=forecast,
    )


def test_renderer_outputs_png(tmp_path: Path) -> None:
    config = _config(tmp_path)
    renderer = Renderer(config)
    snapshot = _snapshot()
    target = config.output_path / "test.png"
    result = renderer.render(snapshot, output_path=target)
    with Image.open(result) as img:
        assert img.size == (config.image_width, config.image_height)
        assert img.mode == "L"


def _periods() -> list[PeriodForecast]:
    labels = ["Morning", "Noon", "Evening", "Night"]
    icons = ["few", "bkn", "shra", "skc"]
    return [
        PeriodForecast(label=label, temp_c=idx + 1, summary="Clear", icon=icons[idx])
        for idx, label in enumerate(labels)
    ]
