# Python code rules

## Language

- Python 3.12+, use modern features: `match` statements, `type X = ...` aliases, exception groups
- Type hints on all public functions and return types. Use `X | None` not `Optional[X]`
- `from __future__ import annotations` in every module

## Style

- Functional/procedural. No classes unless the domain demands it
- Prefer dataclasses for data, plain functions for behavior
- Generators over building lists in memory
- Context managers for anything that needs cleanup
- List comprehensions over `map`/`filter` -- but not nested ones
- `snake_case` everywhere. No abbreviations in public names

## Functions

- Small, single-responsibility. If it needs a comment explaining what it does, split it
- Max 3 parameters. Use a dataclass if you need more
- No boolean flags that change behavior -- make two functions instead
- Pure functions where possible. Side effects at the edges, logic in the center

## Error handling

- Return `None` or a Result type for expected failures. Never raise for control flow
- Catch specific exceptions, never bare `except:`
- Network calls: catch `httpx.HTTPError`, return `None` with the error logged
- Validate at boundaries (CLI input, API responses), trust internal data

## Naming

- Functions: verb phrases (`get_weather`, `parse_response`, `render_dashboard`)
- Variables: descriptive, no single letters except `i`/`x` in comprehensions
- Constants: `UPPER_SNAKE` with `Final` annotation
- Modules: short, lowercase, no underscores if avoidable (`weather.py` not `weather_module.py`)

## Dependencies

- `httpx` for HTTP (not requests)
- `rich` for terminal output
- `click` for CLI
- `pytest` + `respx` for testing
- No dependency without a reason. stdlib first

## Testing

- Tests next to the code they test or in `tests/` mirroring `src/`
- Table-driven tests for multiple input/output combinations
- Mock HTTP calls with `respx`, never hit real APIs in tests
- Test error paths, not just happy paths
- One assertion per test concept -- but multiple asserts on the same object are fine

## Project structure

```
src/dashy/
  __init__.py       -- version, package metadata
  cli.py            -- click entry point, rendering
  models.py         -- shared dataclasses
  http.py           -- shared httpx client factory
  ip.py             -- ipinfo.io module
  weather.py        -- wttr.in module
  news.py           -- RSS feed module
tests/
  test_cli.py
  test_weather.py
  ...
```

## Environment

- Nix flakes for the dev environment (`nix develop`)
- `uv` manages Python dependencies (`uv sync`)
- Justfile recipes call tools by name (`ruff check .`, not `.venv/bin/ruff`)
- `just lint` and `just test` work identically in devShell and CI
