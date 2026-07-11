# UAA Runtime Capability Foundation — Phase 00 Baseline

Status: evidence-backed benchmark baseline. This scorecard grants no runtime
authority and does not change Control Center behavior. Scores measure the
system-level agent stack, not raw model intelligence. Code and tests outweigh
documentation, screenshots, mocks, or aspirations.

Canonical data: `docs/benchmarks/runtime_capability_foundation/phase00_baseline.json`

Benchmark data hash: `sha256:8a7bfbc51f972f138405ba5ead6e12c96dc9d8eff64865a9b5670819963a8ae6`

## Baselines

- UAA: v0.104.0/package 0.104.0 at
  `git-sha:5490fe755a7e9004bca38e6da1c2d91f8e2e4a08`.
- GoatCitadel: v1.0.0 at
  `git-sha:dff26c018b44c394c189c170265a00ab640f1214`, inspected read-only with no
  package import or implementation copying.
- Formula: round-half-up of the weighted 0–10 component scores, normalized to
  100. The 16 weights total 124.

| Repo | Weighted score |
|---|---:|
| UAA | 74.5/100 |
| GoatCitadel | 84.3/100 |

GoatCitadel leads current operational breadth, code/tool execution, extension
depth, and product-loop cohesion. UAA leads exact AuthorityLease governance,
deny-by-default safety, CLI/API contract discipline, and governed bounded
SearXNG/Firecrawl web evidence.

## Component Scorecard

| Component | Weight | UAA | GoatCitadel | Gap owner |
|---|---:|---:|---:|---|
| Reasoning and task understanding | 8 | 5.8 | 7.5 | Phase 01 |
| Planning and orchestration | 8 | 8.1 | 9.0 | Phase 02 |
| Learning and adaptation | 8 | 6.0 | 8.0 | Phase 03 |
| Memory and context management | 9 | 7.6 | 9.0 | Phase 03 |
| Communication and interaction quality | 7 | 7.1 | 8.5 | Phase 08 |
| Action and tool calling | 9 | 7.2 | 9.1 | Phase 04 |
| Autonomy and authority management | 10 | 9.2 | 7.8 | Phase 02 |
| Code and implementation assistance | 6 | 5.8 | 8.5 | Phase 04 |
| Research, web, and external information handling | 5 | 8.3 | 7.0 | Phase 05 |
| Model/provider management | 6 | 6.7 | 8.7 | Phase 05 |
| Evidence, audit, and observability | 9 | 8.7 | 8.5 | Phase 06 |
| Safety, security, and failure handling | 10 | 9.0 | 8.3 | Phase 06 |
| UX as an AI cockpit | 7 | 7.7 | 9.0 | Phase 08 |
| CLI/API parity | 6 | 8.6 | 7.8 | Phase 08 |
| Extensibility and ecosystem | 6 | 5.0 | 8.5 | Phase 07 |
| Productized agent loop | 10 | 6.9 | 9.0 | Phase 02 |

Confidence, maturity status, evidence refs, safe summaries, and gap refs live in
the canonical JSON and are verifier-enforced. UAA evidence refs resolve against
this repository. GoatCitadel refs are pinned to v1.0.0 and syntax-validated
without requiring or mutating a sibling checkout.

## Finite Gap Map

| Phase | Gap | Terminal safe posture |
|---:|---|---|
| 01 | Typed intent and plan revision | Deterministic baseline remains when no exact approved model lane exists. |
| 02 | Bounded Founder Loop completion | Unsafe or missing adapters remain blocked. |
| 03 | Governed context and learning | Hidden injection and automatic memory truth remain blocked. |
| 04 | Useful exact tool/code lanes | Sandbox execution remains blocked without real isolation proof. |
| 05 | Web research/provider observability | Browser, authenticated, paid, and external mutation lanes remain blocked. |
| 06 | Portable content-free evidence | Ed25519 remains blocked without a Keychain-backed lifecycle. |
| 07 | Extension catalog maturity | Arbitrary runtime import remains blocked. |
| 08 | Operator cockpit parity | Linux/Windows remain explicit render placeholders. |
| 09 | Final benchmark and repair | Stop after at most two bounded repair passes. |

## Scenario Contract

The canonical benchmark maps exactly twelve redacted scenarios: ambiguous
intent, plan revision, DAG replay/crash, approval expiry, cancellation race,
budget settlement, tool idempotency, sandbox escape denial, memory correction,
web citation/injection, stale provider, and receipt tamper plus UI/CLI/API
parity. Phase 00 records the contract only; execution evidence is added by its
owning phase and re-run in Phase 09. A truthful blocked result is valid.

## Preservation And Authority Truth

This program preserves WebAccessGateway, exact bounded SearXNG search,
self-hosted one-page Firecrawl markdown, free-plan Firecrawl Cloud,
self-host-first at-most-one eligible fallback, TypeScript 7.0.2, pytest
sharding/timing, mission failure management, and deterministic SSE preview
replay.

All external content remains untrusted evidence and cannot grant authority.
Paid/unknown-plan provider use, browser action, authenticated web, cookies,
downloads/uploads, external mutations, broad host shell, arbitrary plugin
import, and production authority remain denied. Availability, readiness,
health, evidence, UI state, memory, and model output do not authorize an exact
request.

## Preserved Backend Evidence Contracts

Phase 00 keeps the existing backend-owned proof surfaces discoverable while
the new JSON holds the normalized scores:

- `contract-ref:runtime-agent-loop-thread:v1` with
  `scripts/dev/uaa_founder_loop.py inspect-agent-loop`;
- `GET /control-center/runs/observability` with durable retry/recovery posture;
- `contract-ref:runtime-action-tool-code-catalog:v1` with
  `scripts/dev/uaa_founder_loop.py inspect-action-tool-code-catalog`. Generic tool execution remains blocked.
- `contract-ref:runtime-memory-learning-posture:v1` with
  `scripts/dev/uaa_founder_loop.py memory-learning-posture`; memory remains
  recall and reviewable context, not truth or authority;
- `contract-ref:runtime-evidence-audit-spine:v1` with
  `scripts/dev/uaa_founder_loop.py inspect-evidence-audit-spine`; it is a
  content-free read-only lineage surface;
- `contract-ref:runtime-cockpit-cli-api-parity:v1` with
  `scripts/dev/uaa_founder_loop.py inspect-cockpit-parity`; browser automation
  remains blocked; and
- inspectable extension safe refs remain non-callable. Plugin runtime import remains blocked. Connector writes remain blocked. Production authority remains blocked.

## Timing Truth

Phase 00 records same-machine safe timing samples for the tracked-seed pytest
shards, frontend gate, non-live WEB-HYBRID focused set, and Foundation Gate.
The accepted medians are 99.22s for the initial 9,506-test sharded sample,
47.43s for the
frontend gate with 211 tests, 2.90s for 80 non-live WEB-HYBRID tests, and
20.97s for the 627-criterion report-only Foundation Gate. The first shard
attempt was excluded from passing evidence because the isolated worktree lacked
its expected repo-local venv link; the focused environment verifier and all
three accepted shard runs passed after that local setup was corrected.
The final acceptance inventory was 9,528 passed tests. Two later green
diagnostic runs took 127.65s and 143.65s under sustained local load, exceeding
the 15% variance threshold; they are recorded separately and no performance
improvement is claimed.
Timings are diagnostic, hardware-local, and not product-readiness or
performance-improvement claims. No hostname, username, absolute path,
environment dump, or raw log enters the benchmark.

## Stop Contract

Every gap is owned by Phase 01–09 or a terminal blocked posture. Missing score
targets cannot create another phase. After Phase 09 and at most two repair
passes, the program reports honest remaining blockers, merges green intentional
work, leaves a clean pushed `main`, and stops. One optional next program may be
reported but is not activated.
