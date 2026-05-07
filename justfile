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

# build Docker image locally as dashy:dev
docker-build:
    docker build -t dashy:dev .

# run the locally built Docker image
docker-run *ARGS:
    docker run --rm dashy:dev {{ARGS}}

# build and run the Docker image end-to-end
docker-test: docker-build
    docker run --rm dashy:dev
