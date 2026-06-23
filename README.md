# Ultimate AI Agent

**A local-first Founder Command Center for governed AI work.**

[![Build Status](https://img.shields.io/badge/build-placeholder-lightgrey)](#verification)
[![License](https://img.shields.io/badge/license-placeholder-lightgrey)](#license)
[![Version](https://img.shields.io/badge/version-v0.103.0-blue)](VERSION.md)

Ultimate AI Agent helps a single founder/operator plan the day, review safe
action proposals, inspect evidence, and keep agent behavior inside explicit
policy, approval, redaction, and verification boundaries.

Current active baseline: **v0.103.0**. Package version: **0.103.0**.

This repository is active local-first product infrastructure. It does not claim
public beta, public release, public distribution, broad autonomy, connector
writes, unrestricted shell access, or production authority.

## Visual Demo

> Placeholder: add a Control Center GIF or architecture diagram here.

Suggested artifact:

```text
docs/assets/ultimate-ai-agent-control-center-demo.gif
```

## Product Shape

Ultimate AI Agent is the product foundation for a **Founder Command Center**.
The web shell is the **Control Center**. The Python Agent Core remains the
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
- **Local model lane**: llama.cpp/OpenWebUI readiness evidence with local-first limits.
- **Verification gates**: Foundation Gate, OpenAPI, docs, backend, frontend, and product-truth checks.

## Current Technical Snapshot

| Field | Current state |
|---|---|
| Active baseline | **v0.103.0** / `0.103.0` |
| Active program | **Operator Runtime Excellence** |
| Latest repository checkpoint | **checkpoint-m169** |
| Local model lane checkpoints | **checkpoint-m166**, **checkpoint-m167** |
| Local model lane | **M160-M167**, including **M166** production-readiness gate and **M167** live evidence hardening |
| API boundary | FastAPI route contract with **133** OpenAPI paths |
| Founder Loop V1 | `FCC-V1-000` through `FCC-V1-007` complete for bounded proofed route surfaces |
| Governed Cognitive Memory Spine | Phases 1-4 implemented as reviewed/read-only lanes |
| Deferred lane | `UAA-P1-087.2` in-person private UI functional tuning |
| Queued support | `UAA-P1-066` Local Model Control Center inventory/status support |
| Release posture | Local-first, review-gated, disabled by default, non-production by default |

## Tech Stack

| Layer | Technologies | Purpose |
|---|---|---|
| Agent Core | Python 3.10+, Pydantic | Contracts, policy, approval, memory, evidence, and storage logic |
| API | FastAPI, Uvicorn | Local API boundary and `/api/manifest` route metadata |
| Web Shell | React, TypeScript, Vite | Control Center / Founder Command Center UI |
| Frontend Tests | Vitest, Playwright | Component, safety, and interaction checks |
| Backend Tests | pytest, repo verifiers | Contract, storage, route, docs, and product-truth checks |
| Local Tooling | Make, local CLI scripts, npm | Development, launch, inspection, and verification |
| Optional Model Shell | Docker, llama.cpp, OpenWebUI | Local model readiness evidence and secondary shell support |

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
make frontend-check
```

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
| `/today` | Partial | Product spine exists; broader workflow is still staged. |
| `/inbox` | Blocked/future | Connector workflows are not granted. |
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
- **Phase 5**: Context-pack proposals remain planned, not implemented here.
- **Phase 6**: Any execution hook remains future-scoped and blocked.

Memory does not grant truth authority, approval authority, execution authority,
connector authority, CRM/account sync, provider calls, or hidden context
injection.

## Currentness Ledger

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
- UAA-P1-066 remains queued as read-only Local Model Control Center inventory/status support.
- P0-016 hardens tuning advice without granting runtime authority.
- P0-017 adds safe local model operational recovery guidance.

## Documentation

Start with the active product truth and indexes.

| Document | Purpose |
|---|---|
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
docs/archive/releases/v0_103_0/README_IMPORT.md
docs/archive/releases/v0_103_0/master_plan.md
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

- **Phase 5 memory**: context-pack proposals from reviewed L3 refs.
- **Evidence depth**: stronger operator-readable history across more surfaces.
- **Today spine**: tighter Today-to-Actions-to-Evidence loop behavior.
- **Control Center polish**: clearer shell states and fewer raw technical surfaces.
- **Local model support**: safer inventory/status/readiness visibility.
- **Connector contracts**: read-only email/calendar lanes before any write authority.
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
