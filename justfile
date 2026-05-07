# List available recipes
default:
    @just --list

# Lint code with ruff and mypy
lint:
    .venv/bin/ruff check .
    .venv/bin/mypy src/

# Format code with ruff
fmt:
    .venv/bin/ruff format .
    .venv/bin/ruff check --fix .

# Run tests with pytest
test:
    .venv/bin/pytest

# Sync dependencies with uv
sync:
    uv sync --all-extras
