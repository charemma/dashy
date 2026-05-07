# Python project rules

- Python 3.12+, use modern features (match statements, type hints, dataclasses)
- Use `httpx` for HTTP requests (async-capable, modern alternative to requests)
- Use `rich` for terminal output (colors, tables, panels)
- Use `click` for CLI argument parsing
- Tests with `pytest`, use `respx` to mock HTTP calls
- No classes unless the domain demands it -- prefer functions and dataclasses
- Type hints on all public functions
- Keep functions small and focused
