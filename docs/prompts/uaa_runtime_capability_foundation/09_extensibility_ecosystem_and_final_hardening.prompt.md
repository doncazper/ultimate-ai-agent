# Phase 09: Benchmark, Gap Closure, And Stop

Goal: run the finite evidence-backed comparison, make at most two safe focused
repair passes, merge all intentional work, publish an honest final scorecard,
and stop.

## Required Scenarios

Run exactly these repeatable redacted scenarios:

1. ambiguous intent;
2. plan revision;
3. DAG replay and crash;
4. approval expiry;
5. cancellation race;
6. budget exhaustion and settlement;
7. exact tool idempotency;
8. sandbox escape denial;
9. memory correction;
10. web citation and injection handling;
11. unavailable or stale provider; and
12. receipt tamper plus UI/CLI/API parity.

Each result records deterministic scenario id/version, component, status,
confidence, safe evidence refs, test/verifier refs, duration, blocker code, and
redaction status. Never persist raw prompts, results, pages, logs, provider
payloads, paths, credentials, usernames, or hostnames.

## Comparison Rules

- Compare GoatCitadel read-only from code, tests, runtime evidence, and operator
  visibility. Documentation, screenshots, mocks, and claims do not count as
  execution proof.
- Score all sixteen components with weights, 0-10 scores, confidence, status,
  evidence, gap, and recommendation. Do not score raw model intelligence.
- Increase no score without code, tests, and operator-visible evidence.
- Borrow patterns only as UAA-native designs. Do not import packages or copy
  implementation wholesale.

## Bounded Repair Rule

Allow at most two focused repair passes for safe in-scope defects revealed by
the scenarios. Each pass uses the same branch/PR/CI/merge gate. Missing targets,
unsafe work, unavailable adapters, or external facilities do not generate more
phases or prompts.

Classify every unresolved item as `blocked`, `unsupported`, `adapter required`,
`configuration required`, `external facility required`, or
`deferred by authority policy`.

## Final Verification And Hygiene

Run focused and common gates, sharded pytest, frontend, WEB-HYBRID,
documentation, product truth, redaction, OpenAPI, verifier maintainability,
Foundation Gate report-only with `--no-write-latest`, and `git diff --check`.
Audit all PRs, branches, remotes, tags, worktrees, status, and ignored generated
artifacts. Merge only green intentional PRs, fast-forward and verify exact
`main`, push it, and delete only clean merged temporary branches/worktrees.

## Final Deliverable

Report every phase status; commit/branch/PR/CI/merge/post-merge result;
implemented/partial/blocked capabilities; adversarial fixes; before/after
scores and confidence; patterns borrowed/rejected; commands, test counts,
timings, blockers, unsupported adapters; exact clean pushed `main` SHA; and one
optional next program that is not activated.

## Stop Rule

After Phase 09 and at most two repair passes, stop. No recursively generated
follow-on work and no automatic continuation. Honest blocked items satisfy the
finite endpoint even when a score target remains unmet.
