# Architecture

dashy is a small CLI that prints a morning briefing built from three public APIs:
public IP and city (ipinfo.io), current weather (wttr.in), and news headlines
from an RSS feed. The architecture is deliberately simple: three independent
modules behind a thin CLI, glued together by plain function calls.

If something here looks too plain, that is the point. Three API calls and a
terminal renderer do not need a plugin system or dependency injection.

## Directory structure

```
src/dashy/
  __init__.py    # package version
  cli.py         # CLI entry point (click + rich)
  models.py      # data models (dataclasses)
  http.py        # shared httpx client factory
  ip.py          # IP geolocation (ipinfo.io)
  weather.py     # current weather (wttr.in)
  news.py        # RSS news headlines
tests/
  test_cli.py    # CLI smoke tests
  test_*.py      # one test module per src module
docs/
  architecture.md
```

Each data source lives in its own module. The CLI imports them directly. There
is no registry, no plugin loader, no base class.

## Shared HTTP client

All modules go through a single factory in `dashy.http`:

```python
def create_http_client() -> httpx.Client:
    """Create a configured httpx client with timeouts and a User-Agent."""
```

Defaults:

- timeout: 5 seconds (connect, read, write, pool)
- redirects: followed
- `User-Agent: dashy/<version>` so we identify ourselves to free APIs

Modules use the client as a short-lived context manager and let it close itself:

```python
with create_http_client() as client:
    response = client.get(url)
```

No connection pool is shared across modules. The CLI runs once and exits, so the
overhead is negligible and the lifetime is obvious.

## Data models

`dashy.models` defines flat dataclasses, one per module output:

```python
@dataclass(frozen=True)
class IPInfo:
    ip: str
    city: str
    region: str
    country: str

@dataclass(frozen=True)
class Weather:
    temperature_c: int
    condition: str
    wind_speed_kmh: int
    wind_direction: str
    humidity_percent: int

Headlines = list[str]
```

News is the odd one out: a headline is a single string (the title), so the
"model" is just a list of strings rather than a dataclass. This matches the
contract in issue #5 -- title only, no extra fields. If we later need links or
timestamps, we promote `Headlines` to `list[Headline]` with a frozen dataclass
and update the renderer in one place.

Field names on the dataclasses are explicit (`temperature_c`, not `temp`).
Models are frozen so callers cannot mutate them by accident. Anything richer
(weather icons, IP ASN data) is added later by extending the dataclass, not by
changing the call sites.

## Module interfaces

Each data source exposes one function. No classes, no shared state.

```python
# dashy.ip
def get_ip_info() -> IPInfo | None: ...

# dashy.weather
def get_weather(city: str) -> Weather | None: ...

# dashy.news
# Returns at most 5 titles; empty list on any failure or empty feed.
def get_headlines(feed_url: str | None = None) -> Headlines: ...
```

Rules:

- Return a domain object on success, `None` on failure (empty list for news).
- Never raise out of a module. Network errors, timeouts, malformed payloads,
  missing fields all collapse to the failure value.
- No partial dataclasses. If a required field is missing in the response, the
  module returns `None` rather than guessing a default.
- Pure functions: no globals, no caching, no hidden state.

## CLI integration

`dashy.cli.main` is the only place that knows about all three modules. It calls
them in sequence and renders whatever it gets back:

```python
def main() -> None:
    console = Console()

    ip_info = get_ip_info()
    weather = get_weather(ip_info.city if ip_info else DEFAULT_CITY)
    headlines = get_headlines()

    if ip_info:
        render_location(console, ip_info)
    if weather:
        render_weather(console, weather)
    if headlines:
        render_headlines(console, headlines)

    if not (ip_info or weather or headlines):
        console.print("[dim]dashy -- no data available[/dim]")
```

Coupling between modules is intentionally minimal:

- The only real dependency is that weather takes a city, which the IP module
  usually provides.
- If IP fails, weather falls back to a default city constant (or an env var).
- Each render function is local to the CLI; modules do not know about `rich`.

## Error strategy

dashy is a morning briefing, not a debugger. The user wants to see what is
available right now, not a stack trace.

| Failure                       | Module behaviour       | CLI behaviour                |
| ----------------------------- | ---------------------- | ---------------------------- |
| HTTP timeout                  | return `None` / `[]`   | skip that section            |
| Connection refused / DNS      | return `None` / `[]`   | skip that section            |
| 4xx / 5xx response            | return `None` / `[]`   | skip that section            |
| Invalid JSON / malformed XML  | return `None` / `[]`   | skip that section            |
| Required field missing        | return `None`          | skip that section            |
| RSS feed has zero items       | return `[]`            | skip the headlines section   |
| All three fail                | -                      | print "no data available"    |

No retries. No spinners. Exit code is `0` even when sections are missing -- the
CLI succeeded in doing what it could. Logging hooks for debugging are a future
concern; for now silence is the contract.

## Adding a new data source

Three steps. Pattern stays the same whether you add stocks, calendar events, or
the Athens metro status.

### Step 1 -- Define the data model

In `src/dashy/models.py`:

```python
@dataclass(frozen=True)
class StockQuote:
    symbol: str
    price_usd: float
    change_percent: float
```

### Step 2 -- Write the module

Create `src/dashy/stocks.py`:

```python
import httpx

from dashy.http import create_http_client
from dashy.models import StockQuote


def get_stock_quote(symbol: str) -> StockQuote | None:
    """Fetch a quote from example-stocks.com. Returns None on failure."""
    with create_http_client() as client:
        try:
            response = client.get(f"https://example-stocks.com/q/{symbol}")
            response.raise_for_status()
            data = response.json()
            return StockQuote(
                symbol=data["symbol"],
                price_usd=float(data["price"]),
                change_percent=float(data["change_pct"]),
            )
        except (httpx.HTTPError, KeyError, ValueError):
            return None
```

Add a test next to it under `tests/test_stocks.py` that uses `respx` to mock
both the happy path and a failure (timeout or missing field).

### Step 3 -- Wire into the CLI

In `src/dashy/cli.py`:

```python
from dashy.stocks import get_stock_quote

def main() -> None:
    ...
    quote = get_stock_quote("AAPL")
    if quote:
        render_stock_quote(console, quote)
```

That is the whole contract. No registration, no config file, no abstract base
class. If you need to add a fourth, fifth, or tenth source the same three steps
apply.

## Testing

- Tests live under `tests/`, one module per source module.
- `respx` mocks `httpx` calls. No real network in unit tests.
- Each module has at least a happy-path test and a failure test (timeout or
  malformed payload returning the failure value).
- The CLI test layer uses `click.testing.CliRunner` and asserts on rendered
  output for known inputs.

## Non-goals

Things dashy explicitly does not do, and the architecture does not need to
support:

- Concurrent fetches. Three sequential calls finish in well under a second.
- Caching across runs. Morning briefing means fresh data every time.
- Plugin discovery. New sources are code changes, not config changes.
- A daemon or long-running process. The CLI runs once and exits.

If any of these become real requirements later, this document gets revised.
Until then, simplicity wins.
