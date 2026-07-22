# Phase 08: Performance, Supply Chain, And Efficiency

Coverage: P01, P02, P03, P04, P06, P07, P08, P09, P10, L13, and L14.

Objective: establish measured product performance budgets and remove duplicate
work without weakening correctness, authority checks, evidence, redaction, or
test coverage.

## Fresh Baseline Gate

Re-inventory current benchmark scripts, CI performance work, verification
sharding, Control Center profiling, durable worker measurements, memory/search
benchmarks, dependency locks, and overlapping optimization PRs. Record hardware
and environment as safe buckets, not raw host identifiers.

No optimization is accepted without before/after measurements and correctness
regressions. Do not count an unmerged performance branch as baseline.

## Required Performance Work

1. Measure cold/warm Python CLI help and inspection startup, API import/startup,
   `/api/manifest`, first-loop reads, Control Center first readable render,
   route transitions, Memory/Evidence search, durable event replay, worker
   enqueue/claim, Foundation Gate, focused tests, and frontend checks.
2. Identify and defer heavy imports from cold paths without moving policy,
   validation, or redaction after the action boundary.
3. Preserve concurrent read fanout and serialized/single-writer mutations; add
   ordering, failure, cancellation, and resource-limit tests.
4. Inventory every cache. Add bounds, TTL where appropriate, invalidation,
   metrics, deterministic eviction, and shutdown cleanup.
5. Add event/output backpressure and bounded buffers before any live transport
   is called production-ready.
6. Profile Control Center API calls, bundle size, render commits, data
   normalization, and route loading. Split backend reads by route or query only
   when Python truth and coherent revisions are preserved.
7. Benchmark worker queue saturation, claim conflicts, heartbeat cost, approval
   waits, cancellation, restart, and shutdown.
8. Set checked-in warning/failure budgets with calibrated variance. Budgets may
   not disable tests, reduce redaction, skip Foundation Gate, or hide slow
   failures.

## Supply-Chain Work

1. Declare and test supported Node/package-manager versions for Control Center.
2. Require locked Python and Node installations in CI and release workflows.
3. Fail on unexplained lock drift, undeclared direct dependencies, vulnerable
   packages above policy threshold, and missing SBOM/audit evidence.
4. Review the current TypeScript/Vite/Vitest and Python dependency ranges for
   compatibility without downgrading solely to match competitors.
5. Provider, MCP, browser, PTY, and process libraries remain absent from
   production dependencies unless a concrete accepted lane needs them.

## Acceptance Metrics

Record p50/p95, error rate, peak memory, event/order correctness, cache size,
and workload size. Use repeatable local fixtures and at least one real local
product walkthrough. Significant regressions require repair or an explicit
evidence-backed tradeoff; do not simply loosen the budget.

Commit message:

```text
perf(core): enforce measured product and verification budgets
```
