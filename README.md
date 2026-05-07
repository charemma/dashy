# dashy

A morning briefing CLI built entirely by AI agents -- demonstrating [kuromaku](https://github.com/nestrai/kuromaku) (not yet published).

dashy itself is a small Python tool that fetches your IP, weather, and headlines. The interesting part is how it was built: a human filed GitHub issues, kuromaku's agent team designed, implemented, tested, and reviewed everything autonomously. The human reviews PRs and merges -- that is the only manual step.

> Every line of application code in this repo was written, tested, and reviewed by AI agents.
> The human's job: file issues, review PRs, merge.

## Try it

```bash
docker run --rm ghcr.io/charemma/dashy
```

```
dashy  ·  07 May 2026 12:55

Thessaloniki, GR                                        ⛅  21°C  Partly cloudy
Central Macedonia                                    7 km/h S  ·  49% humidity
79.103.140.20

Headlines

  1  Hantavirus-hit cruise ship on way to Canary Islands after three evacuated
  2  Iran considering US proposal as Trump says war will be 'over quickly'
  3  Islamic State-linked women arrive home in Australia from Syria
  4  Shell latest oil giant to see profits surge due to Iran war impact
  5  Israel strikes Beirut for first time since Hezbollah ceasefire
```

Three API calls (ipinfo.io, wttr.in, BBC RSS), no keys needed.

## How it was built

The `.kuro/` directory defines the team, the rules, and the workflow. kuromaku does the rest.

```
.kuro/
  agents/
    Mara.yaml       -- architect (Claude Sonnet)
    Sven.yaml       -- developer (Claude Opus)
    Priya.yaml      -- reviewer (Claude Opus)
    Luna.yaml       -- UX/CLI designer (Claude Sonnet)
  flows/
    implement-issue.yaml   -- the graph workflow
  rules/
    python-style.md        -- Python conventions (type hints, error handling, dependencies)
    clean-code.md          -- design principles (SRP, no magic, fail gracefully)
    git-workflow.md        -- branching and commit rules
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

  pr:
    role: developer
    next:
      - done: "PR opened"
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

## Good to know

- **Verify is deterministic**: exit 0 passes, anything else sends the error output back to the developer. No LLM guessing.
- **Review loops have limits**: if the reviewer keeps rejecting, the flow stops and you get the full transcript.
- **Multi-provider**: agents can run on different LLM providers (Claude, OpenAI, etc.). The workflow is provider-agnostic.
- **The graph self-heals**: review findings, lint failures, test failures all route back to the developer automatically.
- **Rules control quality**: each agent is bound to project rules (python-style.md, clean-code.md). The rules are injected into every prompt. Change the rules, change the output.

## Local setup

```bash
nix develop          # enter dev shell (provides python, uv, ruff, mypy, just)
uv sync              # install Python dependencies
dashy                # run the tool
```

Or build the Docker image locally:

```bash
docker build -t dashy .
docker run --rm dashy
```

## Release

```bash
git tag v0.1.1
git push origin v0.1.1
# CI builds and pushes ghcr.io/charemma/dashy:v0.1.1 + :latest
```

## Issues

See the [issue list](../../issues) for the full build plan.
