# syntax=docker/dockerfile:1.7

# Multi-stage build: dependencies installed with uv in the builder stage,
# only the resulting virtual environment is copied into the runtime image.

FROM python:3.12-slim AS builder

# Pull a pinned uv binary in from the official image instead of installing
# via pip. Keeps the builder layer small and avoids a network roundtrip.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Install third-party dependencies first so this layer is cached as long as
# pyproject.toml and uv.lock do not change.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Now install the project itself. README is referenced from pyproject.toml
# and required by the build backend.
COPY README.md ./
COPY src/ ./src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.source="https://github.com/charemma/dashy" \
      org.opencontainers.image.description="A morning briefing CLI that fetches and displays live data in the terminal" \
      org.opencontainers.image.licenses="MIT"

# Run as a non-root user. dashy only reads from the network, no need for root.
RUN useradd --create-home --uid 1000 dashy
WORKDIR /app

# Copy the prebuilt virtual environment from the builder stage.
COPY --from=builder --chown=dashy:dashy /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER dashy

ENTRYPOINT ["dashy"]
