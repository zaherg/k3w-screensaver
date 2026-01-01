# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder
ENV UV_LINK_MODE=copy
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libfreetype6-dev \
    curl && \
    rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen

FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo \
    zlib1g \
    libfreetype6 && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /app/.venv ./.venv
COPY --from=builder /app/src ./src
COPY pyproject.toml uv.lock README.md ./
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1
VOLUME ["/output"]
ENTRYPOINT ["screensaver"]
CMD ["render", "--output", "/output/kindle-weather.png"]
