# List available recipes
default:
    @just --list

# Lint code with ruff and mypy
lint:
    ruff check .
    mypy src/

# Format code with ruff
fmt:
    ruff format .
    ruff check --fix .

# Run tests with pytest
test:
    pytest

# Sync dependencies with uv
sync:
    uv sync
