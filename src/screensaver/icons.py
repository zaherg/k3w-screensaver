"""Icon helpers for Kindle weather display."""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Final

from PIL import Image, ImageOps

ICON_DIR = Path(__file__).parent / "assets" / "icons"
PNG_DIR = ICON_DIR / "png"
DEFAULT_ICON: Final[str] = "skc"

# Mapping of WWO weather codes to local icon identifiers
CODE_ICON_MAP: dict[str, set[int]] = {
    "skc": {113},
    "few": {116},
    "bkn": {119},
    "ovc": {122},
    "mist": {143},
    "fg": {248, 260},
    "shra": {176, 263, 296, 353, 356},
    "ra": {266, 293, 299, 302},
    "ra1": {305, 308, 359},
    "sn": {179, 227, 230, 323, 326, 329, 332, 335, 338, 368, 371},
    "mix": {182, 185, 317, 320, 362, 365},
    "fzra": {281, 284, 311, 314},
    "ip": {350, 374, 377},
    "tsra": {200, 386, 389, 392, 395},
}


def icon_name_for_code(code: int | None) -> str:
    if not code:
        return DEFAULT_ICON
    for icon, codes in CODE_ICON_MAP.items():
        if code in codes:
            return icon
    return DEFAULT_ICON


@functools.lru_cache(maxsize=64)
def render_icon(icon_name: str, size: int) -> Image.Image:
    png_file = PNG_DIR / f"{icon_name}.png"
    if not png_file.exists():
        png_file = PNG_DIR / f"{DEFAULT_ICON}.png"
    with Image.open(png_file) as img:
        icon = img.convert("LA")
    return ImageOps.contain(icon, (size, size), method=Image.Resampling.LANCZOS)
