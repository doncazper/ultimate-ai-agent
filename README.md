# Ultimate AI Agent

**A local-first governed agent foundation and emerging Control Center for the Founder Loop.**

Ultimate AI Agent helps a single founder/operator plan the day, review safe
action proposals, inspect evidence, and keep agent behavior inside explicit
policy, approval, redaction, and verification boundaries.

Current active baseline: **v0.104.0**. Package version: **0.104.0**.

This repository is a public portfolio view of active local-first product
infrastructure. It demonstrates contract-first AI engineering, product
judgment, governance boundaries, and evidence-backed iteration. It is not a
production autonomous agent platform, public beta, public release, public
distribution, or broad-authority runtime.

## Portfolio Snapshot

| Question | Short answer |
|---|---|
| What is it? | A Python Agent Core with a FastAPI contract boundary, a React/TypeScript Control Center shell, and local-first governance for proposals, approvals, receipts, memory review, and evidence. |
| What does it demonstrate? | API contracts, route classification, local approval authority, idempotency posture, redacted evidence, durable receipts, frontend/backend parity, and disciplined product-language controls. |
| What is usable now? | Exact route-surface proof for `/actions`, `/chat`, `/memory`, and `/evidence`; backend-owned partial inspection surfaces for Start Here, Today, Action Inbox, Proof, Evidence, Memory, Trust, Settings, and local CRM; status surfaces for Runtime and local model readiness; and blocked-state visibility for connector, send/write, and production authority. |
| What is intentionally not claimed? | Production readiness, public release, broad autonomy, connector writes, unrestricted shell/browser/network authority, provider/model authority, hidden context injection, and generic action execution. |

## Product North Star

The current product north star is a calm Control Center for the Founder Loop:
Start Here, Today, Action Inbox, Proof, Evidence, Memory, Trust, Settings,
Plans, Chat, and Setup Assistant. Founder Command Center remains strategy and north-star terminology,
not a separate app shell. The current UI is not yet close to these images. They
are product vision targets, not current implementation screenshots or
implementation evidence; current truth still comes from route/API contracts,
tests, verifiers, and redacted evidence.

See [docs/portfolio/PRODUCT_NORTH_STAR.md](docs/portfolio/PRODUCT_NORTH_STAR.md)
for the full visual target, per-surface truth labels, and current UI gap.

## What This Demonstrates

For AI engineering and applied AI roles, this repo demonstrates:

- Contract-first AI system design around Python core models, FastAPI routes,
  OpenAPI, and `/api/manifest`.
- Human-in-the-loop approval boundaries where approval refs are identifiers
  until exact scope is validated.
- Redacted evidence and receipt posture using safe refs rather than raw
  prompts, raw responses, raw provider payloads, local paths, logs, or secrets.
- Memory as governed recall, not truth or hidden runtime authority.
- CLI/UI parity: operator-relevant Control Center surfaces map back to Python
  core/API contracts and repo-local inspection scripts.
- Product-language honesty across implemented, partial, planned, blocked,
  mock-only, and intentionally out-of-scope states.
- Verifier-backed iteration: docs, route contracts, product truth, frontend
  checks, and safety boundaries are checked as part of the implementation.

## Control Center Preview

These are curated static visual-test snapshots of the local Control Center
shell. They are sanitized demo artifacts, not production screenshots.

| Surface | Preview |
|---|---|
| Setup Assistant | [setup](docs/portfolio/assets/control-center-setup.png) |
| Today | [today](docs/portfolio/assets/control-center-today.png) |
| Action Inbox | [actions](docs/portfolio/assets/control-center-actions.png) |
| Evidence | [evidence](docs/portfolio/assets/control-center-evidence.png) |
| Memory | [memory](docs/portfolio/assets/control-center-memory.png) |

See [docs/portfolio/SCREENSHOTS.md](docs/portfolio/SCREENSHOTS.md) for the
curated gallery and snapshot caveats.

## What Works Today

| Area | Current status | What to inspect |
|---|---|---|
| API boundary | Implemented for the current **242** OpenAPI paths, **243** `/api/manifest` route operations, and route metadata. | [docs/api/README.md](docs/api/README.md) |
| Action Inbox | Backend-owned approve/edit/reject/defer decisions, receipts, evidence refs, and one exact approved local-task AuthorityLease capability. Generic execution remains blocked. | [docs/control_center/FCC_V1_002_ACTION_INBOX_STATE_MACHINE.md](docs/control_center/FCC_V1_002_ACTION_INBOX_STATE_MACHINE.md) |
| Chat handoff | Durable safe Chat turn receipts and reviewable Actions/Plans handoff receipts. Model output is not authority. | [docs/control_center/FCC_V1_004_CHAT_DURABLE_RECEIPT_HANDOFF.md](docs/control_center/FCC_V1_004_CHAT_DURABLE_RECEIPT_HANDOFF.md) |
| Memory | Review receipts, reviewed recall-only records, read-only L1/L2/L3 indexes, proposal-only context packs, and internal Action proposal receipts. Memory remains recall, not truth or authority. | [docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_V1.md](docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_V1.md) |
| Evidence | Productized safe-ref timeline for proposals, decisions, receipts, memory-review events, and one allowlisted Browser/read AuthorityLease-gated WebAccessGateway web evidence preview receipt capability. | [docs/control_center/FCC_V1_006_EVIDENCE_TIMELINE_PRODUCTIZATION.md](docs/control_center/FCC_V1_006_EVIDENCE_TIMELINE_PRODUCTIZATION.md) |
| Today, Plans, Settings, Runtime, Models | Partial/status/readiness surfaces, plus the governed product pilot authority profile for exact local runtime/action/evidence/orchestration capabilities. Useful for inspection, not full product completion. | [docs/control_center/OPERATOR_SHELL_GAP_MAP.md](docs/control_center/OPERATOR_SHELL_GAP_MAP.md) |
| CRM | Backend-owned local CRM command center with read routes, CLI inspection, local storage posture, redacted import/export preview, and one exact local mutation receipt capability. Connector runtime, account sync, sends, calendar writes, provider/model calls, and external CRM writes remain blocked. | [docs/control_center/CRM_LOCAL_COMMAND_CENTER_M2.md](docs/control_center/CRM_LOCAL_COMMAND_CENTER_M2.md) |
| Inbox/email/calendar connectors | Planned or blocked AuthorityLease capability contracts only. No live connector runtime or writes. | [docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md](docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md) |

## Architecture At A Glance

```text
Control Center (React/TypeScript)
  -> FastAPI routes and /api/manifest
  -> Python Agent Core
  -> PolicyEngine + LocalApprovalAuthority
  -> receipts, evidence, memory, storage, and verifier-backed docs

CLI and repo-local scripts inspect the same contracts; React does not mint
authority or own product truth.
```

## What To Review First

| Time | Best path |
|---|---|
| 3 minutes | Read this README, then [docs/portfolio/CURRENT_STATUS.md](docs/portfolio/CURRENT_STATUS.md), [docs/portfolio/PRODUCT_NORTH_STAR.md](docs/portfolio/PRODUCT_NORTH_STAR.md), and [docs/portfolio/GOLDEN_PATH_DEMO.md](docs/portfolio/GOLDEN_PATH_DEMO.md). |
| 10 minutes | Add [docs/portfolio/SCREENSHOTS.md](docs/portfolio/SCREENSHOTS.md), [docs/portfolio/CASE_STUDY.md](docs/portfolio/CASE_STUDY.md), [docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md](docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md), and [docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md](docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md). |
| 30 minutes | Inspect [docs/api/README.md](docs/api/README.md), [docs/control_center/OPERATOR_SHELL_GAP_MAP.md](docs/control_center/OPERATOR_SHELL_GAP_MAP.md), [docs/control_center/PRODUCT_LANGUAGE_RULES.md](docs/control_center/PRODUCT_LANGUAGE_RULES.md), and the focused verifier/test refs linked from those docs. |

## Product Shape

Ultimate AI Agent is the product foundation for a local founder/operator loop.
The web shell is the **Control Center**. The primary workflow inside it is the
**Founder Loop**. Founder Command Center remains strategy and north-star naming,
not a different app or authority layer. The Python Agent Core remains the
authority boundary.

The intended loop is compact:

```text
Morning Briefing
  -> Today Plan
  -> Action Inbox
  -> Reviewable proposal
  -> Approve, edit, reject, or defer
  -> Receipt and Evidence Timeline
  -> Memory Review
  -> Weekly CEO Review
```

## Capability Map

- **Python Agent Core**: policy, approval, route, receipt, and evidence contracts.
- **FastAPI boundary**: typed routes plus `/api/manifest` metadata.
- **Control Center shell**: Today, Actions, Chat, Memory, Evidence, and Settings surfaces.
- **Action envelopes**: exact-scope proposals with approve/edit/reject/defer receipts.
- **Evidence Timeline**: durable history for proposals, decisions, changes, and rollback posture.
- **Memory Review**: accept/correct/reject receipts for reviewed recall only.
- **Governed memory spine**: L1/L2/L3 read-only indexes over safe reviewed refs.
- **Safe workspace previews**: patch proposals, validation proof, and rollback posture.
- **Local model capability posture**: llama.cpp/OpenWebUI readiness evidence with local-first limits.
- **Local CRM capability posture**: backend-owned relationship, follow-up, pipeline, smart-list, report, proposal, import/export-preview, and exact local mutation receipt posture with connector/sends/writes blocked.
- **Governed runtime pilot**: scoped internal RuntimeGateway capabilities for configured loopback local-model receipts, one read-only status command, exact Action Inbox approved focused pytest, repo-verifier, frontend-check, and repo-doctor execution, and approved-runtime-command staged orchestration steps that can consume those exact approved utility capabilities; broad runtime authority remains blocked.
- **Verification gates**: Foundation Gate, OpenAPI, docs, backend, frontend, and product-truth checks.

## Current Technical Snapshot

| Field | Current state |
|---|---|
| Active baseline | **v0.104.0** / `0.104.0` |
| Active program | **Operator Runtime Excellence** |
| Latest repository checkpoint | **checkpoint-m169** |
| Local model lane checkpoints | **checkpoint-m166**, **checkpoint-m167** |
| Local model lane | **M160-M167**, including **M166** local readiness evidence and **M167** live evidence hardening; non-production by default |
| Governed runtime pilot | **UAA-P1-091 / v0.105.0** scoped internal milestone; Phase 07 hardening keeps `v0.104.0` active baseline until the milestone tag is created from green release truth |
| API boundary | FastAPI route contract with **242** OpenAPI paths and **243** manifest route operations |
| Founder Loop V1 | `FCC-V1-000` through `FCC-V1-007` complete for bounded proofed route surfaces |
| Governed Cognitive Memory Spine | Phases 1-5 implemented as reviewed/read-only/proposal capabilities; Phase 6.1 is internal Action proposal receipts only |
| Deferred lane | `UAA-P1-087.2` in-person private UI functional tuning |
| Implemented support | `UAA-P1-066` read-only Local Model Control Center inventory/status support |
| Release posture | Local-first, review-gated, disabled by default, non-production by default |

## Tech Stack

| Layer | Technologies | Purpose |
|---|---|---|
| Agent Core | Python 3.10+, Pydantic | Contracts, policy, approval, memory, evidence, and storage logic |
| API | FastAPI, Uvicorn | Local API boundary and `/api/manifest` route metadata |
| Web Shell | React, TypeScript, Vite | Control Center UI |
| Frontend Tests | Vitest, Playwright | Component, safety, and interaction checks |
| Backend Tests | pytest, repo verifiers | Contract, storage, route, docs, and product-truth checks |
| Local Tooling | Make, local CLI scripts, npm | Development, launch, inspection, and verification |
| Optional Model Shell | Docker, llama.cpp, OpenWebUI, Ollama, MLX-LM | Local model readiness evidence and secondary shell support |

## Quick Start

### Prerequisites

- Python 3.10 or newer.
- `npm` for the Control Center app.
- Optional Docker/OpenWebUI tooling for local model experiments.

### Installation

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
cd apps/control-center
npm install
cd ../..
```

### Environment Setup

Use local development settings only for local development.

```bash
export UAA_ENV=local
```

Do not use local bypass settings as production authority.

### Launch The Control Center

```bash
./scripts/dev/uaa launch-ui
```

This starts or reuses the local backend and Control Center, then opens the
local UI.

### Inspect The Founder Loop

```bash
.venv/bin/python scripts/dev/uaa_founder_loop.py inspect
```

### Inspect The API Contract

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
```

## Verification

Run focused checks before broad gates.

```bash
make doctor
make verify
make verify-fast
make verify-dev-fast
make test-sharded
make verify-dev-sharded
make frontend-check
```

`make verify` preserves the conservative serial all-in verification contract and
remains the release-grade local gate. `make verify-fast` keeps the older serial
local shard composition. `make verify-dev-fast` is the opt-in faster local lane:
it runs `ruff`, `test`, `verify-static`, and `verify-gate-architecture` through
a bounded `make -j$(VERIFY_DEV_FAST_JOBS)` fanout, then generates a serialized
report-only Foundation Gate summary with `--no-write-latest`. It records static
verification timings through `VERIFY_TIMINGS_JSON`, uses the normal non-xdist
pytest suite, and is local verification evidence, not a release-readiness claim
by itself. PR final proof should still include full `make verify` until parallel
equivalence is accepted.

`make test-sharded` is an opt-in local/dev pytest file sharding lane. It uses
`scripts/verification/run_pytest_shards.py` with `PYTEST_SHARDS`, stores
inspectable shard logs and isolated pytest temp dirs under ignored `/tmp`
paths, and writes file timing data to `PYTEST_SHARD_TIMINGS_JSON`. When that
timing file is complete, the runner greedily balances files by prior duration;
when timing data is missing or partial, it falls back to deterministic
file-count sharding. `make verify-dev-sharded` runs the same local/dev
composition through `scripts/verification/run_dev_fast_gate.py`: `ruff`,
sharded pytest, static verification, and gate architecture run in bounded local
fanout, then Foundation Gate runs serialized in report-only mode with
`--no-write-latest`. The runner captures per-phase logs under ignored `/tmp`
paths, writes a timing summary, prints concise pass/fail phase summaries, and
prints detailed log tails when a phase fails. This is local pre-review feedback
only; full `make verify` remains the conservative release-grade proof.

The sharded lane parallelizes the same default-safe contract test posture. It
does not opt into live GGUF search or acquisition, local model root
enumeration, model loading, model benchmarking, llama.cpp startup, OpenWebUI
startup, provider live-network tests, or model-router sweeps. Shard
subprocesses strip known live/model-heavy opt-in environment variables before
pytest starts, so optional live tests remain skipped by default.

No unchanged-file cache shortcut is used by the fast lanes. Any future cache
shortcut needs deterministic invalidation and must remain local/dev-only.

Useful direct checks:

```bash
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_verifier_maintainability.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest --collect-only -q
```

Run Control Center checks when the frontend changes.

```bash
.venv/bin/python scripts/verify_control_center_frontend.py
npm --prefix apps/control-center run test -- --run
```

## Core Boundaries

- Memory is recall, not truth.
- Model output is not authority.
- OpenWebUI is a shell, not authority.
- Control Center UI state is presentation state only unless backed by Python Core/API state.
- Mutating routes must be exact-scoped, idempotent, auditable, and receipt-backed.
- Evidence must use safe refs, redacted summaries, and blocked states.
- Approval refs are identifiers until exact `LocalApprovalAuthority` scope is validated.
- Route side-effect classification and OpenAPI checks are hard boundaries.
- Product claims must follow [docs/control_center/PRODUCT_LANGUAGE_RULES.md](docs/control_center/PRODUCT_LANGUAGE_RULES.md).

## Current Surfaces

| Surface | Status | Notes |
|---|---|---|
| `/actions` | Proofed bounded route surface | Backend-owned decisions and receipts exist. |
| `/chat` | Proofed bounded route surface | Durable receipts and handoff proposals exist. |
| `/memory` | Proofed bounded route surface | Review decisions and L1/L2/L3 read-only indexes exist. |
| `/evidence` | Proofed bounded route surface | Productized timeline events and receipts exist. |
| `/start` | Partial/backend-owned inspection | Start Here binds the repo-safe daily loop to run, proof, action, evidence, memory, and blocked authority refs. |
| `/today` | Partial | Product spine exists; broader workflow is still staged. |
| `/proof` | Partial/backend-owned inspection | Proof index/detail surfaces expose safe refs and blocked authority; they do not grant execution. |
| `/trust` | Partial/backend-owned inspection | Trust is an authority map for enabled, approval-required, planned, and blocked capabilities; it does not grant authority. |
| `/crm` | Partial/backend-owned local | Python-core CRM read model, read-only API routes, CLI inspection, local storage posture, and exact local mutation receipts exist. Connector runtime, external writes, account sync, sends, calendar writes, provider/model calls, live web, browser automation, and production authority remain blocked. |
| `/inbox` | Supporting source-readiness surface | Connector workflows are not granted. |
| `/settings` | Partial/support | Runtime authority is not granted by settings UI. |
| Local models | Partial/support | Readiness evidence only; no broad production authority. |

## Governed Memory Spine

The Governed Cognitive Memory Spine is UAA's local-first, review-gated memory
pipeline. It converts safe, provenance-linked candidates into reviewed recall
records and explainable previews.

- **Phase 1**: Memory Review accept/correct/reject receipts.
- **Phase 2**: L1 hot local memory index for reviewed recall-only records.
- **Phase 3**: L2 factual/graph/temporal projection from L1 safe refs.
- **Phase 4**: L3 identity/session/preference/commitment proposal index.
- **Phase 5**: Read-only, proposal-only context-pack envelopes from reviewed
  safe refs.
- **Phase 6.1**: Exact-approved internal Action proposal receipts only; broader
  execution hooks remain future-scoped and blocked.

Memory does not grant truth authority, approval authority, execution authority,
connector authority, CRM/account sync, provider calls, or hidden context
injection.

## Currentness Ledger

Portfolio readers can treat this as the audit/currentness ledger. It is kept in
the README because repo-local documentation verifiers check these milestone
phrases before release-facing claims are accepted.

These lines keep the active docs and verifiers aligned.

- UAA-P1-067 completes the Today-Spine Founder Command Center beta-readiness planning/currentness pass.
- UAA-P1-068 completes the Today Product Spine Contract.
- UAA-P1-069 completes the Evidence History Grammar contract.
- UAA-P1-070 Memory Source And Provenance Model is complete.
- UAA-P1-071 Memory Review Decision Capture is complete.
- UAA-P1-072 Business Memory And Memory Quality Controls is complete.
- UAA-P1-073 Plans To Reviewable Action Envelopes is complete.
- UAA-P1-074 Chat Local Operator Surface is complete.
- UAA-P1-075 Governed Code Workbench V1 is complete.
- UAA-P1-076 Cross-Surface Memory Intake is complete.
- UAA-P1-077 Memory-To-Loop Binding is complete.
- UAA-P1-078 Private Beta-Readiness Gate is complete as a local/private readiness evidence gate, not a public beta claim.
- UAA-P1-079 User Intent Understanding V1 is complete.
- UAA-P1-080 API Route Classification And Public/Protected Inventory is complete.
- UAA-P1-081 Centralized FastAPI Security Headers is complete.
- UAA-P1-082 Explicit Loopback CORS Allowlist is complete.
- UAA-P1-083 Local Bearer Or Session Gate For Sensitive Routes is complete.
- UAA-P1-084 Mutating Route Idempotency Enforcement Audit is complete.
- UAA-P1-085 Targeted Rate Limits For Expensive And Sensitive Routes is complete.
- UAA-P1-086 API Boundary Enforcement Tests is complete.
- UAA-P1-087.1 Local Launcher Dual-Surface Boot Readiness is complete.
- UAA-P1-087.2a Private Trial Packet And UI Tuning Surface is complete.
- UAA-P1-087.2b Private Trial Findings Capture And Acceptance Ledger is complete.
- UAA-P1-087.2c Private Trial Manual Review Scaffold is complete.
- UAA-P1-091 v0.105.0 Governed Runtime Pilot Phase 07 is the active scoped internal runtime-authority capability set: configured loopback local-model calls, one exact read-only status command, exact Action Inbox approved focused pytest, repo-verifier, frontend-check, and repo-doctor execution, and approved-runtime-command staged orchestration steps for those exact utility capabilities are governed through RuntimeGateway receipts; browser automation, connector writes, plugin import, remote execution, arbitrary shell/subprocess work outside exact approved capabilities, public beta, public release, production authority, and broad autonomy remain blocked.
- UAA-P1-066 is implemented as read-only Local Model Control Center inventory/status support via `GET /control-center/local-models/status`. No lifecycle, switching, activation, downloads, model pulls, model calls, runtime adapters, provider/model authority, or production-readiness claim is added.
- P0-016 hardens tuning advice without granting runtime authority.
- P0-017 adds safe local model operational recovery guidance.

## Documentation

Start with the active product truth and indexes.

| Document | Purpose |
|---|---|
| [docs/portfolio/CASE_STUDY.md](docs/portfolio/CASE_STUDY.md) | Portfolio case study and engineering narrative |
| [docs/portfolio/CURRENT_STATUS.md](docs/portfolio/CURRENT_STATUS.md) | Portfolio-oriented current status summary |
| [docs/portfolio/PRODUCT_NORTH_STAR.md](docs/portfolio/PRODUCT_NORTH_STAR.md) | Current Founder Command Center visual north star |
| [docs/portfolio/SCREENSHOTS.md](docs/portfolio/SCREENSHOTS.md) | Curated static Control Center visual-test snapshot gallery |
| [docs/portfolio/GOLDEN_PATH_DEMO.md](docs/portfolio/GOLDEN_PATH_DEMO.md) | Three-minute demo path through setup, API contracts, approvals, evidence, and CLI parity |
| [docs/releases/TAG_CATALOG.md](docs/releases/TAG_CATALOG.md) | Tag history and future tag convention |
| [docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md) | Full documentation index |
| [docs/canonical/CANONICAL_DOC_MAP.md](docs/canonical/CANONICAL_DOC_MAP.md) | Canonical doc map |
| [docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md](docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md) | Active roadmap |
| [docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md](docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md) | Product truth and blocked states |
| [docs/kanban/current_board.md](docs/kanban/current_board.md) | Current board |
| [docs/control_center/OPERATOR_SHELL_GAP_MAP.md](docs/control_center/OPERATOR_SHELL_GAP_MAP.md) | Control Center shell gap map |
| [docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md](docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md) | Founder Loop V1 milestone truth |
| [docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_V1.md](docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_V1.md) | Governed memory spine contract |
| [docs/api/README.md](docs/api/README.md) | API documentation entrypoint |
| [docs/api/openapi_contract.md](docs/api/openapi_contract.md) | OpenAPI contract |
| [docs/api/route_inventory.md](docs/api/route_inventory.md) | Route inventory |
| [SECURITY.md](SECURITY.md) | Security posture |
| [docs/security/SECURITY_TRIAGE_RUNBOOK.md](docs/security/SECURITY_TRIAGE_RUNBOOK.md) | Security triage runbook |

Current archived release packet refs:

```text
docs/archive/releases/v0_104_0/README_IMPORT.md
docs/archive/releases/v0_104_0/master_plan.md
```

## Operational References

| Area | Document |
|---|---|
| M167 live evidence | [docs/production/M167_LIVE_MODEL_EVIDENCE_MATRIX.md](docs/production/M167_LIVE_MODEL_EVIDENCE_MATRIX.md) |
| Local model smoke harness | [docs/production/M167_LOCAL_MODEL_E2E_SMOKE_HARNESS.md](docs/production/M167_LOCAL_MODEL_E2E_SMOKE_HARNESS.md) |
| Release latency baseline | [docs/production/RELEASE_LATENCY_BASELINE_HARNESS.md](docs/production/RELEASE_LATENCY_BASELINE_HARNESS.md) |
| Release verification lanes | [docs/production/RELEASE_VERIFICATION_LANES.md](docs/production/RELEASE_VERIFICATION_LANES.md) |
| Release evidence packet | [docs/production/RELEASE_EVIDENCE_PACKET.md](docs/production/RELEASE_EVIDENCE_PACKET.md) |
| Backup/restore verification | [docs/production/BACKUP_RESTORE_VERIFICATION.md](docs/production/BACKUP_RESTORE_VERIFICATION.md) |
| Local state rollback | [docs/production/LOCAL_STATE_ROLLBACK_RUNBOOK.md](docs/production/LOCAL_STATE_ROLLBACK_RUNBOOK.md) |
| Local runtime packaging | [docs/production/LOCAL_RUNTIME_PACKAGING.md](docs/production/LOCAL_RUNTIME_PACKAGING.md) |
| Plugin/skill boundary | [docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md](docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md) |
| Inspectable extension catalog | [docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md](docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md) |
| Extension activation grants | [docs/tooling/EXTENSION_ACTIVATION_GRANTS.md](docs/tooling/EXTENSION_ACTIVATION_GRANTS.md) |
| MCP/A2A compatibility watchlist | [docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md](docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md) |
| llama-server packaging provenance | [docs/production/LLAMA_SERVER_PACKAGING_PROVENANCE_CHECKLIST.md](docs/production/LLAMA_SERVER_PACKAGING_PROVENANCE_CHECKLIST.md) |
| Local model operational runbook | [docs/production/LOCAL_MODEL_OPERATIONAL_RUNBOOK.md](docs/production/LOCAL_MODEL_OPERATIONAL_RUNBOOK.md) |

## Historical Roadmap Anchors

These M34-M60 labels are historical audit anchors. They are not the active
package baseline.

| Release | Milestone |
|---|---|
| v0.38.0 | M34 - Broader File Capability Review |
| v0.39.0 | M35 - Safe File Review Workflow Contracts |
| v0.40.0 | M36 - CCC File Review Surface, Review-Only |
| v0.41.0 | M37 - Review Approval Capture, Review-Only Persistence |
| v0.42.0 | M38 - Safe Context Proposal From Approved Review |
| v0.43.0 | M39 - CCC Context Proposal Surface |
| v0.44.0 | M40 - Context Handoff Approval, No Injection |
| v0.45.0 | M41 - Local Prototype Safety Freeze |
| v0.46.0 | M42 - Mobile Companion Product Contract Refresh |
| v0.47.0 | M43 - Mobile API Boundary, Read-Only |
| v0.48.0 | M44 - CCC iOS Skeleton, No Authority |
| v0.49.0 | M45 - CCC iOS Local Read-Only Connection |
| v0.50.0 | M46 - iOS Review/Receipt Read-Only Surfaces |
| v0.51.0 | M47 - TestFlight Pipeline, Internal Only |
| v0.52.0 | M48 - First Internal TestFlight Build |
| v0.53.0 | M49 - Mobile Review Approval Capture |
| v0.54.0 | M50 - Mobile Approval Audit Hardening |
| v0.55.0 | M51 - OpenWebUI Bridge Adapter Pilot |
| v0.56.0 | M52 - OpenWebUI Safe Conversation Surface |
| v0.57.0 | M53 - Controlled Tool Expansion Review |
| v0.58.0 | M54 - Safe Media Metadata Inspector |
| v0.59.0 | M55 - Redacted Observability Export |
| v0.60.0 | M56 - Agent Eval Regression Harness |
| v0.61.0 | M57 - Runtime Sandbox Architecture Review |
| v0.62.0 | M58 - Dry-Run Execution Audit Harness |
| v0.63.0 | M59 - Public GitHub Readiness |
| v0.64.0 | M60 - Local Developer Beta Freeze |

## Project Layout

```text
apps/control-center/      React + TypeScript Control Center shell
docs/                     Roadmaps, contracts, release truth, and indexes
scripts/                  Local launch, verification, and inspection scripts
src/ultimate_ai_agent/    Python Agent Core and FastAPI API
tests/                    Backend, contract, storage, verifier, and API tests
```

## Roadmap

- **Memory follow-through**: keep Phase 5 context-pack proposals review-only
  while shaping future exact-approved Phase 6 hooks.
- **Evidence depth**: stronger operator-readable history across more surfaces.
- **Today spine**: tighter Today-to-Actions-to-Evidence loop behavior.
- **Control Center polish**: clearer shell states and fewer raw technical surfaces.
- **Local model support**: safer inventory/status/readiness visibility.
- **Connector contracts**: read-only email/calendar capabilities before any write authority.
- **Private UI testing**: deferred `UAA-P1-087.2` functional tuning after more implementation evidence.

## Contributing

Keep changes scoped.

1. Read [AGENTS.md](AGENTS.md).
2. Preserve policy, approval, route, OpenAPI, redaction, and Foundation Gate boundaries.
3. Update the smallest relevant docs and indexes.
4. Add focused tests for behavior changes.
5. Update OpenAPI/API manifest truth for route changes.
6. Run focused checks before broader gates.
7. Avoid public beta, production, connector-write, provider/model, and broad autonomy claims.

## License

License placeholder. Add the final project license file before any public
distribution claim.
