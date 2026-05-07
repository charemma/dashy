# Python project rules

- Python 3.12+, use modern features (match statements, type hints, dataclasses)
- Use `httpx` for HTTP requests (async-capable, modern alternative to requests)
- Use `rich` for terminal output (colors, tables, panels)
- Use `click` for CLI argument parsing
- Tests with `pytest`, use `respx` to mock HTTP calls
- No classes unless the domain demands it -- prefer functions and dataclasses
- Type hints on all public functions
- Keep functions small and focused

# Environment

- This project uses Nix flakes for the dev environment (`nix develop`)
- `uv` manages Python dependencies (`uv sync` to install)
- The Nix devShell provides all tools: python, uv, ruff, mypy, just, pytest
- Justfile recipes must call tools by name only (e.g. `ruff check .`, NOT `.venv/bin/ruff check .`) -- the devShell puts them in PATH
- Never hardcode `.venv/bin/` paths in the justfile or scripts
- `just lint` and `just test` must work identically inside `nix develop` and in CI
