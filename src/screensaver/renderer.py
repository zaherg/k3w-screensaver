"""Rendering utilities for the Kindle PNG."""

from __future__ import annotations

from datetime import datetime, time
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

from .config import AppConfig
from .models import DailyForecast, PeriodForecast, WeatherSnapshot

FORECAST_PERIOD_LABELS = ["Morning", "Noon", "Evening", "Night"]
from .icons import render_icon


class FontManager:
    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path
        self._cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}

    def get(self, size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
        key = (weight, size)
        if key not in self._cache:
            filename = (
                "AtkinsonHyperlegible-Bold.ttf"
                if weight == "bold"
                else "AtkinsonHyperlegible-Regular.ttf"
            )
            self._cache[key] = ImageFont.truetype(
                str(self._base_path / filename),
                size=size,
            )
        return self._cache[key]


class Renderer:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        fonts_path = Path(__file__).parent / "assets" / "fonts"
        self.fonts = FontManager(fonts_path)
        self.padding = 32
        self.gutter = 12
        self.current_icon_size = 150
        self.forecast_icon_size = 56
        self.forecast_card_width = 150
        self.forecast_card_height = 180
        self.forecast_cards_per_row = 3

    def render(self, snapshot: WeatherSnapshot, *, output_path: Path) -> Path:
        mode = "L" if self.config.grayscale else "RGB"
        image = Image.new(
            mode=mode,
            size=(self.config.image_width, self.config.image_height),
            color=255,
        )
        draw = ImageDraw.Draw(image)
        y = self.padding
        y = self._draw_header(draw, snapshot, y)
        y += self.gutter
        y = self._draw_current(draw, image, snapshot, y)
        y += self.gutter
        footer_y = self.config.image_height - self.padding - 20
        forecast_height = 240
        forecast_y = footer_y - forecast_height - self.gutter
        self._draw_forecast(draw, image, snapshot.forecast, forecast_y, forecast_height)
        self._draw_footer(draw, snapshot, footer_y)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, format="PNG")
        return output_path

    def _draw_header(
        self,
        draw: ImageDraw.ImageDraw,
        snapshot: WeatherSnapshot,
        y: int,
    ) -> int:
        location_font = self.fonts.get(36, "bold")
        info_font = self.fonts.get(20, "regular")
        draw.text(
            (self.padding, y),
            snapshot.location_name,
            font=location_font,
            fill=0,
        )
        header_text = _format_datetime(snapshot.current.observation_time)
        text_width = draw.textlength(header_text, font=info_font)
        draw.text(
            (
                self.config.image_width - self.padding - text_width,
                y + 10,
            ),
            header_text,
            font=info_font,
            fill=0,
        )
        return y + location_font.size + 10

    def _draw_current(
        self,
        draw: ImageDraw.ImageDraw,
        image: Image.Image,
        snapshot: WeatherSnapshot,
        y: int,
    ) -> int:
        current = snapshot.current
        temp_font = self.fonts.get(140, "bold")
        text_font = self.fonts.get(22, "regular")
        temp_text = f"{current.temperature_c}°c"
        icon_x = self.padding + 40
        icon_y = y + 20
        self._paste_icon(image, current.icon, icon_x, icon_y, self.current_icon_size)
        text_x = icon_x + self.current_icon_size + 40
        draw.text((text_x, y), temp_text, font=temp_font, fill=0)

        block_y = y + temp_font.size + 8
        info_lines = [
            f"Feels like {current.feels_like_c}°c",
            f"Chance of rain {current.chance_of_rain}%",
            f"Cloud cover {current.cloud_cover}%",
            f"{current.summary}",
        ]
        for line in info_lines:
            draw.text((text_x, block_y), line, font=text_font, fill=0)
            block_y += text_font.size + 6

        return max(block_y, icon_y + self.current_icon_size)

    def _draw_forecast(
        self,
        draw: ImageDraw.ImageDraw,
        image: Image.Image,
        forecasts: Iterable[DailyForecast],
        y: int,
        height_available: int,
    ) -> None:
        days = list(forecasts)[:3]
        if not days:
            return
        label_width = 80
        available_width = (self.config.image_width - 2 * self.padding - label_width) * 0.75
        col_count = len(days)
        col_width = max(
            90, (available_width - (col_count - 1) * self.gutter) // col_count
        )
        total_width = col_width * col_count + self.gutter * (col_count - 1) + label_width
        table_start_x = self.padding + max(0, (self.config.image_width - 2 * self.padding - total_width) / 2)
        col_start_x = table_start_x + label_width
        header_font = self.fonts.get(16, "bold")
        label_font = self.fonts.get(16, "bold")
        temp_font = self.fonts.get(16, "bold")
        summary_font = self.fonts.get(14, "regular")
        icon_size = 26
        header_y = y
        for idx, day in enumerate(days):
            col_x = col_start_x + idx * (col_width + self.gutter)
            text = day.date.strftime("%a %d")
            draw.text(
                (col_x, header_y),
                text,
                font=header_font,
                fill=0,
            )
        row_y = header_y + header_font.size + 8
        period_labels = FORECAST_PERIOD_LABELS
        row_height = max((height_available - header_font.size - 20) / len(period_labels), icon_size + 14)
        period_maps = [
            {period.label: period for period in day.periods} for day in days
        ]
        for label in period_labels:
            draw.text(
                (self.padding + label_width / 2, row_y + row_height / 2),
                label,
                font=label_font,
                fill=0,
                anchor="mm",
            )
            for idx in range(col_count):
                period = period_maps[idx].get(
                    label,
                    PeriodForecast(label=label, temp_c=0, summary="", icon="skc"),
                )
                col_x = col_start_x + idx * (col_width + self.gutter)
                icon_x = col_x + 6
                icon_y = row_y + row_height / 2 - icon_size / 2
                self._paste_icon(image, period.icon, icon_x, icon_y, icon_size)
                center_x = icon_x + icon_size + (col_width - icon_size - 12) / 2
                text_y = row_y + row_height / 2 - (temp_font.size + summary_font.size + 4) / 2
                draw.text(
                    (center_x, row_y + row_height / 2),
                    f"{period.temp_c}°c",
                    font=temp_font,
                    fill=0,
                    anchor="mm",
                )
            row_y += row_height

    def _draw_footer(
        self,
        draw: ImageDraw.ImageDraw,
        snapshot: WeatherSnapshot,
        y: float,
    ) -> None:
        footer_font = self.fonts.get(16, "regular")
        footer = (
            f"Updated {snapshot.generated_at.strftime('%Y-%m-%d')} "
            f"{_format_ampm(snapshot.generated_at)} UTC"
        )
        draw.text(
            (self.padding, int(y)),
            footer,
            font=footer_font,
            fill=0,
        )

    def _paste_icon(
        self,
        image: Image.Image,
        icon_name: str,
        x: int,
        y: int,
        size: int,
    ) -> None:
        icon = render_icon(icon_name, size)
        luminance = icon.getchannel("L")
        mask = icon.getchannel("A")
        image.paste(luminance, (int(x), int(y)), mask=mask)


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def _format_datetime(dt: datetime) -> str:
    return f"{dt.strftime('%a %d %b')} {_format_ampm(dt)}"


def _format_ampm(value: datetime | time) -> str:
    formatted = value.strftime("%I:%M %p")
    if formatted.startswith("0"):
        formatted = formatted[1:]
    return formatted
