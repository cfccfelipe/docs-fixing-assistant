.PHONY: test lint format clean run

test:
	uv run pytest tests/unit -q --tb=line

test-integration:
	uv run pytest tests/integration -q --tb=line

lint:
	uv run ruff check src tests
	uv run mypy src

format:
	uv run ruff format src tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

run:
	uv run start-app
