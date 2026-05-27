.PHONY: install dev test lint format clean build

# Default target
all: install

# Install the package
install:
	uv sync

# Install with dev dependencies
dev:
	uv sync --extra dev

# Run tests
test:
	uv run pytest

# Run tests with coverage
test-cov:
	uv run pytest --cov=src --cov-report=term-missing --cov-report=html

# Lint code
lint:
	uv run ruff check src/

# Format code
format:
	uv run ruff format src/
	uv run ruff check src/ --fix

# Type check
typecheck:
	uv run mypy src/

# Clean build artifacts
clean:
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Build distribution
build: clean
	uv build

# Development workflow
watch:
	uv run pytest -w

# Pre-commit hooks
hooks:
	uv run pre-commit install

# Help
help:
	@echo "Available targets:"
	@echo "  install    - Install dependencies"
	@echo "  dev        - Install with dev dependencies"
	@echo "  test       - Run tests"
	@echo "  test-cov   - Run tests with coverage"
	@echo "  lint       - Lint code"
	@echo "  format     - Format code"
	@echo "  typecheck  - Type check code"
	@echo "  clean      - Clean build artifacts"
	@echo "  build      - Build distribution"
	@echo "  hooks      - Install pre-commit hooks"