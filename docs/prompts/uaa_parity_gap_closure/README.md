# UAA Hermes/OpenClaw Parity Gap Closure Prompt Pack

Status: stored execution prompts, not runtime authority

Purpose: close the implementation, reliability, performance, and product gaps
identified by the July 14, 2026 UAA comparison with Hermes Agent and OpenClaw.
This is a delta-closure program, not a second roadmap and not a request to
reimplement work that another branch, pull request, or Codex task has already
landed.

The pack executes a fresh convergence inventory before every implementation
phase. Only code merged into the current `main`, covered by meaningful tests,
and exposed through the required Python Core/API/CLI/Control Center surfaces
counts as complete. Contracts, plans, mock data, disabled adapters, static
renders, open pull requests, and unmerged branches do not count as implemented
runtime behavior.

## Wrapper Command

From the repository root:

```bash
bash scripts/dev/run_uaa_parity_gap_closure_prompt_pack.sh --allow-network
```

The non-dry-run wrapper fails before invoking Codex unless network access is
explicitly authorized with `--allow-network`. The wrapper accepts only the
`workspace-write` sandbox, disables web search, and constrains spawned-command
egress through Codex's allowlist-first network proxy to GitHub-owned endpoints
needed for fetch, push, PR, CI, review, and merge gates. Dry-run and list
operations remain offline.

Validate and emit the combined pack without invoking Codex:

```bash
bash scripts/dev/run_uaa_parity_gap_closure_prompt_pack.sh --dry-run
```

List the ordered prompt files:

```bash
bash scripts/dev/run_uaa_parity_gap_closure_prompt_pack.sh --list
```

## Prompt Order

1. `00_execute_parity_gap_closure_end_to_end.prompt.md`
2. `01_fresh_inventory_and_convergence_ledger.prompt.md`
3. `02_backend_truth_first_loop_and_evidence.prompt.md`
4. `03_live_local_setup_and_packaging.prompt.md`
5. `04_goals_durable_events_and_lifecycle.prompt.md`
6. `05_action_inbox_work_board_and_session_ux.prompt.md`
7. `06_morning_briefing_sources_and_background_worker.prompt.md`
8. `07_memory_search_backup_and_storage_integrity.prompt.md`
9. `08_performance_supply_chain_and_efficiency.prompt.md`
10. `09_cross_cutting_reliability_and_future_lane_proofs.prompt.md`
11. `10_end_to_end_acceptance_and_parity_truth.prompt.md`

Use Prompt 00 for a single continuous run. The verified combined snapshot keeps
the validated manifest and all phase instructions stable for that run. Before
each phase, synchronize and
reinspect repository/code state from `main` so merged work from other tasks is
incorporated rather than repeated; do not replace the snapshot's prompt text
or manifest with mutable worktree content.

## Convergence And Non-Duplication Contract

Before every phase, inspect:

- current local and remote `main` SHA;
- dirty files, staged files, worktrees, local branches, and remote branches;
- open and recently merged pull requests, their files, reviews, and checks;
- in-progress branches that overlap the phase;
- current capability, release-surface, route-status, authority, and operational
  maturity manifests;
- existing implementation, tests, verifiers, CLI commands, APIs, OpenAPI,
  receipts, and Control Center wiring; and
- active Codex tasks when task-list/read tools are available.

Classify every work item as exactly one of:

- `merged_proven`
- `merged_partial`
- `open_pr_owned_elsewhere`
- `in_flight_branch_owned_elsewhere`
- `mock_or_contract_only`
- `planned_only`
- `blocked_by_authority`
- `blocked_by_external_facility`
- `missing`
- `superseded`

Only `merged_proven` may be skipped as complete. An item is
`merged_proven` only when the current `main` contains the behavior, focused
tests pass, operator surfaces use backend-owned data, and all required
authority/evidence/CLI/API contracts are satisfied. A phase that is entirely
`merged_proven` creates no empty commit or pull request; it records its proof in
the convergence ledger and proceeds.

Never modify, merge, close, or supersede an overlapping pull request owned by
another task unless that work is explicitly handed to this program. Continue
with independent work and revisit the overlap after the next `main` refresh.

## Live-Data And No-Mock Completion Floor

Production completion requires:

- real Python-owned durable state or a real accepted adapter;
- no `mockControlCenterData`, static sample, placeholder receipt, or generated
  preview as the success path;
- truthful unavailable, stale, blocked, or disconnected UI when a real source
  is absent;
- API and CLI inspection of the same backend state shown by Control Center;
- stable OpenAPI operation IDs, `/api/manifest` metadata, route side-effect
  classification, and tests;
- redacted durable evidence with source, revision, time, and verification refs;
- approval, exact scope, idempotency, replay, cancellation, rollback or
  rollback-readiness, and safe-disable behavior for every mutation; and
- a real end-to-end acceptance test or dogfood path, not only a unit contract.

Test fixtures may exist only in tests. A loopback or temporary-directory test
is not enough by itself when the feature claims an external live-data adapter.
The production adapter must exist, be accepted by an exact authority milestone,
and fail closed when it is unavailable.

## Authority Boundary

This stored pack promotes nothing by itself. Runtime model calls, provider SDK
calls, unrestricted web access, browser automation, arbitrary shell execution,
connector writes, plugin execution, remote execution, background production
authority, and public distribution remain blocked unless a separate accepted
exact-scoped milestone grants that exact lane.

When a work item requires new authority, the execution program must verify an
already accepted lane or request a separate authority decision. It must not use
this pack, a roadmap entry, an approval ref, competitor behavior, or the user's
desire for parity as authority. A blocked lane does not stop independent phases,
but it cannot be counted complete or replaced with a mock.

## Complete Coverage Matrix

### Recommended for UAA from Hermes

| ID | Recommendation | Phase |
|---|---|---:|
| H01 | Persistent founder/operator goals | 04 |
| H02 | Durable read-only event stream | 04 |
| H03 | Atomic memory mutation audit and hardening | 07 |
| H04 | Narrow background briefing worker | 06 |
| H05 | Real local packaging/setup lane | 03 |
| H06 | LLM-free cross-session search | 07 |

### Recommended for UAA from OpenClaw

| ID | Recommendation | Phase |
|---|---|---:|
| O01 | Persistent goal lifecycle | 04 |
| O02 | Strict backend-truth mode | 02 |
| O03 | Durable event cursor and lifecycle | 04 |
| O04 | Local backup, verify, and restore | 07 |
| O05 | Work Board live reconciliation | 05 |
| O06 | Delivery-evidence contract for future connectors | 09 |
| O07 | Better session UX | 05 |
| O08 | Governed Morning Briefing source refresh | 06 |

### Performance Optimizations

| ID | Optimization | Phase |
|---|---|---:|
| P01 | Lazy imports and cold/warm startup budgets | 08 |
| P02 | Read fanout with serialized writes and ordering tests | 08 |
| P03 | Compact reads and denser local search | 07, 08 |
| P04 | Bounded cache concurrency, TTL, and invalidation | 08 |
| P05 | Duplicate provider/image-call prevention | 09 |
| P06 | Abort-aware network, polling, and adapter cancellation | 08, 09 |
| P07 | Event/output backpressure | 04, 08 |
| P08 | Durable-worker queue/claim efficiency | 06, 08 |
| P09 | Frontend duplicate-work and route-loading reduction | 08 |
| P10 | CI and test-speed budgets without coverage loss | 08 |

### Bug Fixes UAA May Need

| ID | Bug class | Phase |
|---|---|---:|
| B01 | Approval scope and owner ambiguity | 09 |
| B02 | Missing approval module or fail-open adapter | 09 |
| B03 | Ambiguous send causing duplicate delivery | 09 |
| B04 | Restart fence or admission state left closed | 04, 09 |
| B05 | Stale session UI or mock-masked backend loss | 02, 09 |
| B06 | Streaming ordering and UTF-8 boundary corruption | 04, 09 |
| B07 | Provider fallback retry after possible side effects | 09 |
| B08 | Memory drift and concurrent writes | 07, 09 |
| B09 | Storage budgets ignoring sidecars/backups | 07, 09 |
| B10 | Export, archive, or restore path traversal | 07, 09 |
| B11 | Secrets split across log/event chunks | 09 |
| B12 | Autosave overwriting invalid or stale state | 05, 09 |
| B13 | Approval-wait expiry and orphaned work | 04, 09 |
| B14 | Stale evidence or optimistic completion | 02, 09 |

### UAA-Specific Implementation Backlog

| ID | Backlog item | Phase |
|---|---|---:|
| L01 | Remove mock success paths from critical product truth | 02 |
| L02 | Complete real Setup/Packaging lane | 03 |
| L03 | Complete readable first founder loop | 02 |
| L04 | Prevent stale/fallback evidence appearing verified | 02 |
| L05 | Harden Action Inbox approval-envelope UX | 05 |
| L06 | Add persistent goals/plans | 04 |
| L07 | Add durable live event replay/stream | 04 |
| L08 | Add governed Morning Briefing sources | 06 |
| L09 | Add Work Board revisioning and live reconciliation | 05 |
| L10 | Product-prove worker lifecycle and recovery | 04, 06 |
| L11 | Add verified local backup/restore | 07 |
| L12 | Harden memory concurrency, drift, migration, and ranking | 07 |
| L13 | Establish product performance budgets | 08 |
| L14 | Enforce locked supply-chain changes | 08 |
| L15 | Improve Chat/session UX after truth gates | 05 |
| L16 | Add redacted cross-session search | 07 |

## Finite Endpoint

The pack contains Phase 01 through Phase 10. Each non-no-op phase produces one
scoped branch, commit series, pull request, green hosted checks, merge, and
post-merge verification before the next phase. Phase 10 permits at most two
focused repair passes. It then stops with an honest terminal ledger; it does
not generate another prompt pack or silently defer incomplete P0/P1 work.

## Bundle Verification

```bash
.venv/bin/python scripts/verify_uaa_parity_gap_closure_prompt_pack.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_uaa_parity_gap_closure_prompt_pack.py -q
```
