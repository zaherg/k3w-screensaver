> **Note:** This codebase and README were produced with OpenAI’s **GPT-5 Codex** assistant (reasoning level: high).

# Kindle Weather Screensaver

Generate a **600×800 8-bit grayscale PNG** tailored for the Kindle 3 WiFi (B008) that shows today's weather and the next few days. Data is fetched from [wttr.in](https://wttr.in) for a configurable latitude/longitude, rendered via Pillow, then optionally uploaded to Cloudflare R2.

## Features
- wttr.in JSON ingestion with cached fallback for offline rendering.
- Typography/layout tuned for Kindle e-ink (Atkinson Hyperlegible fonts bundled).
- Weather symbols derived from Matthew Petroff’s Kindle Weather Display icon set (CC0), pre-rendered into grayscale PNGs.
- Forecast table shows the next three days broken into morning/noon/evening/night periods with custom icons.
- CLI built with Typer + `uv`; ships as a Docker image for cron execution.
- Automatic upload to Cloudflare R2 (S3-compatible). No local storage is required when running inside Docker.
- GitHub Actions workflow builds and pushes the Docker image to GHCR on every push to `main`.

## Requirements
- Python 3.11+ with [`uv`](https://github.com/astral-sh/uv) installed.
- wttr.in latitude/longitude coordinates.
- (Optional) Cloudflare R2 account, bucket, and API credentials.

## Setup
```bash
uv sync
cp .env.example .env  # fill in LATITUDE/LONGITUDE/etc.
```

## CLI Usage
Render locally (writes into `output/` by default):
```bash
uv run screensaver render
```
Common flags:
- `--output /path/to/file.png` – override output location.
- `--offline` – skip network call and reuse cached wttr payload.
- `--upload/--no-upload` – force (or skip) Cloudflare upload regardless of `.env`.
- `--key yyyy/mm/dd/custom.png` – override R2 object key (prefix handled by config).

## Cloudflare R2 configuration
Set the following env vars (see `.env.example`):
- `R2_UPLOAD=true`
- `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET` and optional `R2_KEY_PREFIX`
- `R2_ENDPOINT_URL` (or leave blank to derive from account id)

## Docker / Deployment
### GitHub Actions
A workflow at `.github/workflows/docker-publish.yml` builds the project with `docker buildx` and pushes to `ghcr.io/zaherg/k3w-screensaver` automatically on every push to `main` (or via manual dispatch). No extra setup beyond enabling GitHub Packages is required.

### Cron (host scheduler)
Use your host's crontab to run the container on a schedule. Because the CLI uploads to R2, no local volume is required.

One-line run (no cron):
```bash
docker run --rm --name k3w-screensaver --env-file /path/to/.env ghcr.io/zaherg/k3w-screensaver:main render --output /output/kindle-weather.png
```

Edit your crontab:
```bash
crontab -e
```
Example entry (run at minute 58 of every hour, kill any stuck run, then render):
```bash
58 * * * * /usr/bin/docker rm -f k3w-screensaver >/dev/null 2>&1 || true; /usr/bin/docker run --rm --name k3w-screensaver --env-file /path/to/.env ghcr.io/zaherg/k3w-screensaver:main render --output /output/kindle-weather.png
```
If cron can't find Docker, use the full path to `docker` (as above) or set `PATH` in your crontab.

### Manual build
```bash
uv run python -m pip install buildx  # if needed
docker build -t k3w-screensaver .
docker run --rm --env-file .env k3w-screensaver --output /tmp/kindle.png
```

## Development
```bash
make lint    # Ruff
make test    # Pytest suite
make format  # Ruff format
```

## Assets
- Fonts: [Atkinson Hyperlegible](https://github.com/googlefonts/atkinson-hyperlegible) (OFL 1.1) included in `src/screensaver/assets/fonts/`.
- Weather icons: Adapted from [Matthew Petroff’s Kindle Weather Display](https://mpetroff.net/2012/09/kindle-weather-display/) and released under CC0; see `src/screensaver/assets/icons/README`.
