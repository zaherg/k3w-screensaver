"""Configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(slots=True)
class R2Config:
    enabled: bool
    account_id: str | None
    access_key_id: str | None
    secret_access_key: str | None
    bucket: str | None
    key_prefix: str
    endpoint_url: str | None


@dataclass(slots=True)
class AppConfig:
    latitude: float
    longitude: float
    location_name: str
    image_width: int
    image_height: int
    grayscale: bool
    cache_dir: Path
    output_path: Path
    r2: R2Config
    wttr_base_url: str


def load_config() -> AppConfig:
    load_dotenv()
    cache_dir = Path(".cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    output = Path("output")
    output.mkdir(parents=True, exist_ok=True)
    latitude = float(_get_env("LATITUDE", required=True))
    longitude = float(_get_env("LONGITUDE", required=True))
    location_name = _get_env("LOCATION_NAME", default="Your Location")
    wttr_base_url = _get_env("WTTR_BASE_URL", default="https://wttr.in")
    r2 = _load_r2_config()
    return AppConfig(
        latitude=latitude,
        longitude=longitude,
        location_name=location_name,
        image_width=600,
        image_height=800,
        grayscale=True,
        cache_dir=cache_dir,
        output_path=output,
        r2=r2,
        wttr_base_url=wttr_base_url,
    )


def _load_r2_config() -> R2Config:
    enabled = _get_env("R2_UPLOAD", default="false").lower() == "true"
    account_id = _get_env("R2_ACCOUNT_ID")
    endpoint_url = _get_env("R2_ENDPOINT_URL")
    if not endpoint_url and account_id:
        endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
    return R2Config(
        enabled=enabled,
        account_id=account_id or None,
        access_key_id=_get_env("R2_ACCESS_KEY_ID"),
        secret_access_key=_get_env("R2_SECRET_ACCESS_KEY"),
        bucket=_get_env("R2_BUCKET"),
        key_prefix=_get_env("R2_KEY_PREFIX", default="screensaver"),
        endpoint_url=endpoint_url,
    )


def _get_env(name: str, *, required: bool = False, default: str | None = None) -> str:
    from os import getenv

    value = getenv(name)
    if value:
        return value
    if default is not None:
        return default
    if required:
        raise RuntimeError(f"Missing required environment variable {name}")
    return ""
