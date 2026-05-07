default:
    @just --list

install:
    uv sync

lint:
    uv run ruff check .
    uv run mypy src/

fmt:
    uv run ruff format .
    uv run ruff check --fix .

test:
    uv run pytest
