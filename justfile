venv := ".venv"

default:
    @just --list

install:
    uv sync

lint:
    {{venv}}/bin/ruff check .
    {{venv}}/bin/mypy src/

fmt:
    {{venv}}/bin/ruff format .
    {{venv}}/bin/ruff check --fix .

test:
    {{venv}}/bin/pytest
