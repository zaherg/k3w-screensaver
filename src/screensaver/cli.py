"""Command line interface for Kindle weather renderer."""

from __future__ import annotations

from datetime import datetime
import logging
from pathlib import Path
from typing import Annotated

import typer

from .config import AppConfig, load_config
from .renderer import Renderer
from .uploader import R2Uploader
from .wttr import WttrClient

app = typer.Typer(add_completion=False, help="Generate Kindle-ready weather PNG.")


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


@app.callback()
def main(
    ctx: typer.Context,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable verbose logging."),
    ] = False,
) -> None:
    """Initialize CLI context."""
    ctx.obj = {"verbose": verbose}
    _configure_logging(verbose)


@app.command()
def render(
    ctx: typer.Context,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            exists=False,
            dir_okay=False,
            writable=True,
            help="Path to write the PNG (defaults to output/ folder).",
        ),
    ] = None,
    offline: Annotated[
        bool,
        typer.Option("--offline", help="Use cached wttr payload only."),
    ] = False,
    upload: Annotated[
        bool | None,
        typer.Option(
            "--upload/--no-upload",
            help="Override default upload behavior.",
        ),
    ] = None,
    key: Annotated[
        str | None,
        typer.Option(
            "--key",
            help="Override R2 object key (without prefix).",
        ),
    ] = None,
) -> None:
    """Render the Kindle screensaver image."""
    config = load_config()
    client = WttrClient(config)
    snapshot = client.fetch(use_cache_only=offline)
    renderer = Renderer(config)
    target = output or _default_output_path(config, snapshot.generated_at)
    rendered_path = renderer.render(snapshot, output_path=target)
    typer.echo(f"Saved {rendered_path}")

    should_upload = upload if upload is not None else config.r2.enabled
    if should_upload:
        uploader = R2Uploader(config.r2)
        object_key = key or _default_object_key(snapshot.generated_at)
        stored_key = uploader.upload(rendered_path, object_key=object_key)
        typer.echo(f"Uploaded to r2://{config.r2.bucket}/{stored_key}")


def _default_output_path(config: AppConfig, generated_at: datetime) -> Path:
    return config.output_path / "kindle-weather.png"


def _default_object_key(generated_at: datetime) -> str:
    return "kindle-weather.png"
