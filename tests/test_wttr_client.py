from __future__ import annotations

import json
from pathlib import Path

from screensaver.config import AppConfig, R2Config
from screensaver.wttr import WttrClient


def _test_config(tmp_path: Path) -> AppConfig:
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    return AppConfig(
        latitude=41.0,
        longitude=28.0,
        location_name="Test City",
        image_width=600,
        image_height=800,
        grayscale=True,
        cache_dir=cache_dir,
        output_path=output_dir,
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


def test_parse_payload(tmp_path: Path) -> None:
    config = _test_config(tmp_path)
    client = WttrClient(config)
    payload = json.loads(
        (Path(__file__).parent / "data" / "wttr-sample.json").read_text()
    )
    snapshot = client._parse_payload(payload)  # type: ignore[attr-defined]

    assert snapshot.location_name == "Test City"
    assert snapshot.current.temperature_c == 2
    assert snapshot.current.summary == "Partly cloudy"
    assert snapshot.current.icon == "few"
    assert snapshot.current.chance_of_rain == 45
    assert len(snapshot.forecast) == 2
    first = snapshot.forecast[0]
    assert first.max_c == 4
    assert first.chance_of_rain == 45
    assert first.sunrise.strftime("%H:%M") == "08:30"
    assert first.icon == "few"
    assert len(first.periods) == 4
    assert first.periods[0].label == "Morning"
