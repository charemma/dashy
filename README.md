# dashy -- kuromaku demo project

This repo demonstrates how [kuromaku](https://github.com/nestrai/kuromaku) (not yet published) works. An AI agent team builds a Python CLI tool from nothing but GitHub issues. No human writes code -- the agents design, implement, test, review, and open PRs autonomously.

The tool being built (`dashy`) is secondary. The point is the process: file an issue, run the workflow, get a PR.

## How it works

1. A human creates a GitHub issue describing what to build
2. `kuro run implement-issue --var id=<issue>` starts the workflow
3. The agent team works through a graph flow:

```
design (Mara, architect)
  -> implement (Sven, developer)
    -> verify (shell: just lint && just test)
      -> review (Priya, reviewer on OpenAI Codex)
        -> open draft PR
```

Each step feeds its output to the next. If verify fails, it loops back to implement. If review finds problems, it sends the code back. The graph handles all the routing -- the human just files issues and reviews PRs.

## What is kuromaku?

A CLI tool for reproducible AI agent teams. You define your team in YAML or Markdown, write rules they follow, and run workflows that turn issues into PRs. Think of it as CI/CD for AI-assisted development.

## Repo structure

```
.kuro/                    -- this is all kuromaku needs
  agents/                 -- who is on the team
    Mara.yaml             -- architect (Claude)
    Sven.yaml             -- developer (Claude)
    Priya.yaml            -- reviewer (OpenAI Codex)
  flows/                  -- how they work together
    implement-issue.md    -- the graph flow in Markdown format
  rules/                  -- what rules they follow
    python-style.md       -- Python conventions for this project
    git-workflow.md       -- branching and commit rules
```

Everything under `src/`, `tests/`, `pyproject.toml`, `justfile`, etc. is created by the agents through issues.

## The demo tool

`dashy` is a morning briefing CLI that fetches live data from REST APIs:

```
$ dashy

  Location    Athens, GR (203.0.113.42)

  Weather     24C sunny, Wind 12 km/h NW

  Headlines
    EU agrees on new AI regulation framework
    Champions League semifinal results
```

Three API calls, no keys needed (ipinfo.io, wttr.in, RSS feed), displayed with rich terminal formatting.

## Issues

See the [issue list](../../issues) for the build plan. Each issue is a self-contained unit of work that the agent team picks up and delivers as a PR.
