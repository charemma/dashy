# Clean code principles

## Single responsibility

Every function does one thing. Every module has one reason to change.
If you are writing a function that fetches data AND formats it, split it.

## No magic

No magic numbers or strings. Use named constants with `Final`:

```python
# bad
if len(headlines) > 5:

# good
MAX_HEADLINES: Final = 5
if len(headlines) > MAX_HEADLINES:
```

## DRY but not over-abstract

Don't repeat yourself, but three similar lines are better than a premature
abstraction. Extract only when the pattern appears three or more times
AND the abstraction has a clear name.

## Separation of concerns

- I/O at the edges (cli.py, http.py)
- Business logic in the middle (weather.py, ip.py, news.py)
- Data definitions separate (models.py)
- Never mix HTTP calls with rendering or parsing with I/O

## Dependencies point inward

- `cli.py` imports from `weather.py`, never the other way around
- Modules do not import from `cli.py`
- `models.py` imports nothing from the project
- `http.py` imports nothing from the project

## Fail gracefully

Each data source can fail independently. The CLI shows what is available
and marks the rest as unavailable. Never crash because one API is down.

## Readability over cleverness

Write code a junior developer understands on first read. No nested
ternaries, no chained walrus operators, no clever one-liners that
save a line but cost five minutes of reading.
