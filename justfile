default:
    @just --list

# install Python dependencies
install:
    uv sync

# run linters (ruff + mypy)
lint:
    ruff check .
    uv run mypy src/

# format code
fmt:
    ruff format .
    ruff check --fix .

# run tests
test:
    uv run pytest

# run the CLI
run *ARGS:
    uv run dashy {{ARGS}}
