---
format: kuromaku-flow/v1
---

# implement-issue

Implement issue #{{vars.id}} in this repository.
Follow the project rules and produce a draft PR at the end.

---

## design
*role: architect*

Read issue #{{vars.id}} with `gh issue view {{vars.id}} --comments`.

Produce a short design plan: affected files, interfaces, edge
cases, and testing strategy. Do not write code.

-> implement: plan complete, ready to build
-> aborted: missing context, cannot plan

---

## implement
*role: developer*

Implement the design from the previous step. Write clean,
idiomatic Python with type hints. Add tests that cover the
new behavior. Commit with conventional commit messages.

-> verify: implementation complete, run checks
-> design: design flaw discovered during implementation
-> aborted: cannot proceed safely

---

## verify
*run: just lint && just test*

-> review: pass
-> implement: fail

---

## review
*role: reviewer*

Review the implementation against the issue's acceptance
criteria. Check that tests cover the behavior and the code
is clean. If something is off, send it back.

-> pr: all criteria met, code quality acceptable
-> implement: changes needed
-> design: wrong approach, needs redesign
-> aborted: review cannot complete

---

## pr
*role: developer*

Push the branch and open a draft PR with `Closes #{{vars.id}}`.
Output the PR URL on its own line.

-> done: PR opened
-> aborted: PR creation failed

---

## done
*final: implementation reviewed, draft PR is open*

---

## aborted
*final: a step could not proceed safely*
