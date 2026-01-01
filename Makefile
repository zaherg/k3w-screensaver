.PHONY: lint test render format

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests

render:
	uv run screensaver render --output output/sample.png --offline

test:
	uv run pytest
