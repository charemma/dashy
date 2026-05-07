# syntax=docker/dockerfile:1.7
# Multi-stage build: dependencies installed in the builder stage, runtime
# image only carries the resolved virtualenv plus the dashy package.

FROM python:3.12-slim AS builder

# Install uv from the official distroless image. Pinning to a specific tag
# keeps builds reproducible across runs.
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /usr/local/bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

# Install runtime dependencies first so the layer is cached when only the
# source changes. --no-install-project skips installing dashy itself here.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Now bring in the source and install the package itself into the venv.
COPY src ./src
COPY README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


FROM python:3.12-slim AS runtime

# Run as an unprivileged user; dashy needs no root capabilities.
RUN useradd --create-home --uid 1000 dashy

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=builder /opt/venv /opt/venv

USER dashy
WORKDIR /home/dashy

ENTRYPOINT ["dashy"]
