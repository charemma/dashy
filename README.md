# dashy

A morning briefing CLI built entirely by AI agents -- demonstrating [kuromaku](https://github.com/nestrai/kuromaku) (not yet published).

dashy itself is a small Python tool that fetches your IP, weather, and headlines. The interesting part is how it was built: a human filed GitHub issues, kuromaku's agent team designed, implemented, tested, and reviewed everything autonomously. The human reviews PRs and merges.

## The tool

```
$ dashy

  dashy  morning briefing    07 May 2026 12:30

  Location               Weather
  Thessaloniki, GR       20C  Partly cloudy
  79.103.140.20          Wind 4 km/h W, Humidity 52%

  Headlines
  1. Hantavirus-hit cruise ship on way to Canary Islands
  2. Iran considering US proposal as Trump says war will be 'over quickly'
  3. Islamic State-linked women arrive home in Australia from Syria
```

Three API calls (ipinfo.io, wttr.in, BBC RSS), no keys needed.

## How it was built

The `.kuro/` directory defines the team and the workflow. kuromaku does the rest.

```
.kuro/
  agents/
    Mara.yaml       -- architect (Claude Sonnet)
    Sven.yaml       -- developer (Claude Opus)
    Priya.yaml      -- reviewer (OpenAI)
  flows/
    implement-issue.yaml   -- the graph workflow
  rules/
    python-style.md        -- conventions the agents follow
```

The workflow is a graph. Each step either succeeds and moves forward, or gets sent back:

```yaml
# simplified from .kuro/flows/implement-issue.yaml
graph:
  design:
    role: architect
    next:
      - implement: "plan complete"

  implement:
    role: developer
    next:
      - verify: "implementation complete"
      - design: "design flaw found"

  verify:
    run: just lint && just test
    next:
      - review: pass
      - implement: fail          # failed checks -> back to developer

  review:
    role: reviewer
    next:
      - pr: "approved"
      - implement: "changes needed"  # reviewer can send it back
```

## Example: building the weather module

```
$ kuro run implement-issue --var id=4

  [design]     Mara    1m53s   -> implement    plan complete
  [implement]  Sven    2m16s   -> verify       implementation complete
  [verify]     shell   2.0s    -> review       exit 0
  [review]     Priya   1m46s   -> implement    architecture violations found
                                               ^^^^^^^^^^^^^^^^^^^^^^^^^^
  [implement]  Sven    2m44s   -> verify       fixed
  [verify]     shell   3.8s    -> review       exit 0
  [review]     Priya   1m11s   -> pr           approved
  [pr]         Sven    31.2s   -> done         PR #15 opened

  flow complete   8 steps   10m29s
```

Priya sent Sven back because he built his own HTTP client instead of using the shared one from the architecture doc. He fixed it, second review passed. No human typed anything between `kuro run` and `PR opened`.

The human's role: file issues, review the PR, merge. The agents handle design, code, tests, and review.

## Good to know

- **Verify is deterministic**: exit 0 passes, anything else sends the error output back to the developer. No LLM guessing.
- **Review loops have limits**: if the reviewer keeps rejecting, the flow stops and you get the full transcript.
- **Multi-provider**: Mara and Sven run on Claude (Anthropic), Priya runs on OpenAI. The workflow is provider-agnostic.
- **The graph self-heals**: review findings, lint failures, test failures all route back to the developer automatically. The graph handles retry logic.

## Setup

```bash
nix develop          # enter dev shell (provides python, uv, ruff, mypy, just)
uv sync              # install Python dependencies
dashy                # run the tool
```

## Issues

See the [issue list](../../issues) for the full build plan.
