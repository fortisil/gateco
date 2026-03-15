.PHONY: dev test lint format clean install

install:
	pip install -e ".[dev]"

dev:
	uvicorn src.gateco.main:app --reload --port 8000

test:
	pytest -v

test-cov:
	pytest --cov=src/gateco --cov-report=html

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
