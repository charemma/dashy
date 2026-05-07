# dashy -- morning briefing CLI

Demo project showing how [kuromaku](https://github.com/nestrai/kuromaku) orchestrates an AI agent team to build software from GitHub issues.

## What this demonstrates

An AI team (architect, developer, reviewer) builds a Python CLI tool by working through GitHub issues autonomously. Each issue goes through a graph flow:

```
design -> implement -> verify (lint + test) -> review -> PR
```

The team is defined in `.kuro/`, the workflow in `.kuro/flows/`. A human files issues, the agents do the rest.

## The tool being built

`dashy` -- a command-line morning briefing that fetches live data from REST APIs and displays it in the terminal.

```
$ dashy

  Location    Athens, GR (203.0.113.42)

  Weather     24C sunny
              Wind 12 km/h NW, Humidity 45%

  Headlines
    EU agrees on new AI regulation framework
    Champions League semifinal results
    Greek economy grows 2.3% in Q1
```

Three data sources, one clean output:
- **IP geolocation** via ipinfo.io (no API key needed)
- **Weather** via wttr.in (no API key needed)
- **News headlines** via a public RSS feed

## Project structure

```
.kuro/
  agents/       -- agent personas (architect, developer, reviewer)
  flows/        -- workflow graph (implement-issue)
  rules/        -- project rules the agents follow
src/
  dashy/         -- the Python CLI
tests/
justfile        -- task runner (lint, test, fmt)
pyproject.toml  -- project config
```
