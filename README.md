# Ultimate AI Agent

**A local-first governed agent foundation for a founder/operator control loop.**

Ultimate AI Agent (UAA) pairs a Python Agent Core with a TypeScript Control
Center shell, typed FastAPI contracts, approval boundaries, redacted evidence,
rollback posture, and verifier-backed release discipline. The goal is simple:
make agent work inspectable, permissioned, reversible, and testable before it
can affect local state.

This repository is under active development. It is **not** a public release,
public beta, hosted production service, broad-autonomy runtime, unrestricted
tool runner, connector-write runtime, or production-authority system.

## Snapshot

| Field | Current state |
|---|---|
| Active baseline | **v0.103.0** / package `0.103.0` |
| Latest repository checkpoint | **checkpoint-m169** |
| Local model lane checkpoints | **checkpoint-m166**, **checkpoint-m167** |
| Active program | **Operator Runtime Excellence** |
| Product direction | **Founder Command Center** for a single-user founder/operator loop |
| API boundary | FastAPI route contract with **126** OpenAPI paths |
| Proofed Control Center surfaces | `/actions`, `/chat`, `/memory`, and `/evidence` for exact backend-owned route-surface behavior |
| Partial or blocked surfaces | `/today` is partial; `/inbox`, `/settings`, model lifecycle, connector workflows, and action execution remain partial, blocked, or future-scoped |
| Runtime posture | Contract-first, validation-first, preview/review-oriented |
| Production readiness | Not claimed |

Detailed release truth lives in the
[Product Release-Truth Packet](docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md).
Operator-facing copy follows the
[Control Center Product Language Rules](docs/control_center/PRODUCT_LANGUAGE_RULES.md).

<details>
<summary>Baseline audit anchors</summary>

Current completed/queued task anchors:

- UAA-P1-067 completes the Today-spine, memory-first beta-readiness
  planning/currentness pass.
- UAA-P1-068 completes the Today Product Spine Contract.
- UAA-P1-069 completes the Evidence History Grammar.
- UAA-P1-070 Memory Source And Provenance Model is complete.
- UAA-P1-071 Memory Review Decision Capture is complete.
- UAA-P1-072 Business Memory And Memory Quality Controls is complete.
- UAA-P1-073 Plans To Reviewable Action Envelopes is complete.
- UAA-P1-074 Chat Local Operator Surface is complete.
- UAA-P1-075 Governed Code Workbench V1 is complete.
- UAA-P1-076 Cross-Surface Memory Intake is complete.
- UAA-P1-077 Memory-To-Loop Binding is complete.
- UAA-P1-078 Private Beta-Readiness Gate is complete.
- UAA-P1-079 User Intent Understanding V1 is complete.
- UAA-P1-080 API Route Classification And Public/Protected Inventory is
  complete.
- UAA-P1-081 Centralized FastAPI Security Headers is complete.
- UAA-P1-082 Explicit Loopback CORS Allowlist is complete.
- UAA-P1-083 Local Bearer Or Session Gate For Sensitive Routes is complete.
- UAA-P1-084 Mutating Route Idempotency Enforcement Audit is complete.
- UAA-P1-085 Targeted Rate Limits For Expensive And Sensitive Routes is
  complete.
- UAA-P1-086 API Boundary Enforcement Tests is complete.
- UAA-P1-087.1 Local Launcher Dual-Surface Boot Readiness is complete.
- UAA-P1-087.2a Private Trial Packet And UI Tuning Surface is complete.
- UAA-P1-087.2b Private Trial Findings Capture And Acceptance Ledger is
  complete.
- UAA-P1-087.2c Private Trial Manual Review Scaffold is complete.
- UAA-P1-066 remains queued as strictly read-only Local Model Control Center
  inventory/status support.
- P0-016 hardens tuning advice for lag, out-of-memory, crash loop, reload
  loop, slow token rate, and one-change rollback cases without granting
  runtime authority.
- P0-017 adds safe local model operational recovery guidance for safe,
  degraded, blocked, and unsupported states.

Required evidence links:

- [Release latency baseline harness](docs/production/RELEASE_LATENCY_BASELINE_HARNESS.md)
- [Release evidence packet](docs/production/RELEASE_EVIDENCE_PACKET.md)
- [Backup/restore verification](docs/production/BACKUP_RESTORE_VERIFICATION.md)
- [Local state rollback runbook](docs/production/LOCAL_STATE_ROLLBACK_RUNBOOK.md)
- [llama-server packaging/provenance checklist](docs/production/LLAMA_SERVER_PACKAGING_PROVENANCE_CHECKLIST.md)
- [Local model operational runbook](docs/production/LOCAL_MODEL_OPERATIONAL_RUNBOOK.md)
- [Plugin/skill ecosystem boundary](docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md)
- [Inspectable extension catalog](docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md)
- [Extension activation grants](docs/tooling/EXTENSION_ACTIVATION_GRANTS.md)
- [MCP/A2A compatibility watchlist](docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md)

Historical M34-M60 labels remain audit anchors, not the active baseline:

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

</details>

## Why It Matters

UAA is built for high-trust local agent work, not broad unattended automation.
Its strongest product ideas are:

- **Python Agent Core as authority**: Control Center and OpenWebUI are shells;
  product behavior stays behind core/API contracts.
- **Typed route metadata**: `/api/manifest`, OpenAPI, route classifications,
  side-effect classes, auth posture, approval posture, idempotency posture, and
  verifier checks keep the API boundary visible.
- **Approval-bound mutations**: `PolicyEngine` and `LocalApprovalAuthority`
  remain hard gates for work that can change local state.
- **Evidence as history**: receipts, safe refs, redacted summaries, and
  Evidence Timeline entries explain what was proposed, decided, changed, can be
  undone, is stale, or remains blocked.
- **CLI parity**: operator-relevant workflows must have a Python core/API
  contract and command-line or repo-local script inspection path.
- **Local-first model posture**: llama.cpp/OpenWebUI support is scoped to local
  readiness and compatibility evidence; OpenWebUI does not own product state.

## Where Things Stand

| Area | Current state | Start here |
|---|---|---|
| API perimeter | UAA-P1-080 through UAA-P1-086 cover route classification, security headers, loopback CORS, local bearer gate, idempotency header gate, targeted local rate limits, and API boundary enforcement tests. | [API docs](docs/api/README.md), [route inventory](docs/api/route_inventory.md) |
| Founder Loop V1 | FCC-V1-000 through FCC-V1-007 prove a bounded route-surface lane for Actions, Chat, Memory, and Evidence. | [Founder Loop milestones](docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md) |
| Action Inbox | Backend-owned approve/edit/reject/defer decision state, idempotency posture, receipt refs, and Evidence Timeline visibility exist; action execution remains blocked. | [Action Inbox state machine](docs/control_center/FCC_V1_002_ACTION_INBOX_STATE_MACHINE.md) |
| Today-to-Action loop | A Today item can become a reviewable Action envelope and produce decision receipts; the broader Today product surface remains partial. | [Founder Loop vertical slice](docs/control_center/FCC_V1_003_FOUNDER_LOOP_VERTICAL_SLICE.md) |
| Chat | Durable safe Chat turn receipts and reviewable Actions/Plans handoff receipts exist; model output is not truth, approval, memory, or execution authority. | [Chat receipt and handoff](docs/control_center/FCC_V1_004_CHAT_DURABLE_RECEIPT_HANDOFF.md) |
| Memory Review | Accept/correct/reject decisions are backend-owned and receipt-backed; automatic memory writes, context injection, CRM/account sync, and connector writes remain blocked. | [Memory Review decisions](docs/control_center/FCC_V1_005_MEMORY_REVIEW_DECISIONS.md) |
| Evidence | Evidence Timeline productization is present for the Founder Loop events; evidence remains read-only, safe-ref-only review material. | [Evidence Timeline productization](docs/control_center/FCC_V1_006_EVIDENCE_TIMELINE_PRODUCTIZATION.md) |
| Control Center shell | The product cockpit direction is Today, Inbox, Plans, Actions, Memory, Evidence, Settings, Models, and future first-party Chat. Route truth is explicit; several surfaces remain partial or blocked. | [Operator shell gap map](docs/control_center/OPERATOR_SHELL_GAP_MAP.md) |
| Local model lane | Local model work is scoped to readiness evidence, inventory/status inspection, and compatibility paths; lifecycle controls and production-readiness claims remain blocked. | [M167 evidence matrix](docs/production/M167_LIVE_MODEL_EVIDENCE_MATRIX.md), [local model scope](docs/model_management/UAA_P1_064_LOCAL_MODEL_INVENTORY_READ_ONLY.md) |
| Release discipline | Foundation Gate, OpenAPI checks, documentation integrity, product-truth checks, and focused tests are release-facing boundaries. | [Release verification lanes](docs/production/RELEASE_VERIFICATION_LANES.md) |

## Founder Loop Spine

The accepted product spine is intentionally narrow:

```text
Today item
  -> reviewable Action envelope
  -> exact approve/edit/reject/defer decision
  -> durable receipt ref
  -> Evidence Timeline update
  -> CLI/repo-local inspection path
```

This proves the first readable operator loop without granting action execution,
connector writes, shell/subprocess execution, provider/model authority, memory
writes, public beta, public distribution, or production authority.

## Architecture

```text
Operator / Control Center
        |
        v
FastAPI route contract and /api/manifest
        |
        v
Python Agent Core
        |
        +-- PolicyEngine and LocalApprovalAuthority
        +-- durable run records, event ledger refs, receipts, replay refs
        +-- safe workspace previews and approval-bound patch proposals
        +-- local model readiness lane for llama.cpp/OpenWebUI
        +-- redacted observability under .uaa/
```

Control Center is the first-party product cockpit. OpenWebUI is a supported
local/dev conversational shell and compatibility surface only. Product state,
approval posture, and authority boundaries stay with the Python Agent Core.

## What Is Not Claimed

The current baseline does not grant:

- production authority, public release, public beta, or public distribution
- broad autonomy or autonomous background sessions by default
- unrestricted shell/subprocess execution
- unrestricted network access or browser automation
- connector writes outside exact reviewed scopes
- plugin runtime import or arbitrary plugin execution
- mobile control or mobile sensor runtime
- model/provider/OpenWebUI output as approval, truth, memory, or execution
  authority
- raw prompt, response, provider payload, local path, log, username, hostname,
  serial, environment dump, credential material, or secret-like values in
  durable evidence

Future expansion must name the exact milestone, authority boundary, approval
model, persistence model, tests, verifier updates, and rollback or safe-disable
plan.

## Where Things Are Going

The next product lane is the Founder Command Center path:

- harden the local Control Center macOS-first Setup Assistant
- improve first product loop readability across Today, Actions, Memory, and
  Evidence
- refine Action Inbox and approval-envelope UX
- build out the Morning Briefing skeleton with bounded local summaries
- add read-only email/calendar integration contracts later, without connector
  writes or account authority
- continue local model inventory/status work as read-only Control Center
  support before any lifecycle controls

Planning references:

- [Founder Command Center master plan](docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md)
- [Founder Command Center MVP spec](docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md)
- [Founder Command Center board](docs/kanban/founder_command_center_board.md)
- [Phase 0/1 tasks](docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md)
- [Target product architecture](docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md)

## Quick Start

Set up a local development environment:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
cd apps/control-center && npm install && cd ../..
```

Run focused verification for the current API/docs boundary:

```bash
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
```

Run aggregate checks:

```bash
make verify
make frontend-check
```

For local runtime packaging guidance, start with
[Local Runtime Packaging](docs/production/LOCAL_RUNTIME_PACKAGING.md). The
packaging path is loopback-first local readiness only; it does not claim public
distribution, hosted production support, or signed installer readiness.

## Documentation Map

| Need | Read |
|---|---|
| Docs home | [docs/README.md](docs/README.md) |
| Full documentation index | [docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md) |
| Canonical doc map | [docs/canonical/CANONICAL_DOC_MAP.md](docs/canonical/CANONICAL_DOC_MAP.md) |
| Current roadmap | [docs/canonical/09_roadmap.md](docs/canonical/09_roadmap.md) |
| Active product truth | [Product Release-Truth Packet](docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md) |
| Operator Runtime Excellence | [roadmap](docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md), [current board](docs/kanban/current_board.md) |
| Control Center status | [gap map](docs/control_center/OPERATOR_SHELL_GAP_MAP.md), [route status manifest](docs/control_center/ROUTE_STATUS_MANIFEST.md), [language rules](docs/control_center/PRODUCT_LANGUAGE_RULES.md) |
| API boundary | [API docs](docs/api/README.md), [OpenAPI contract](docs/api/openapi_contract.md), [route inventory](docs/api/route_inventory.md) |
| Local model lane | [M167 hardening](docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING.md), [E2E smoke harness](docs/production/M167_LOCAL_MODEL_E2E_SMOKE_HARNESS.md), [llama-server checklist](docs/production/LLAMA_SERVER_PACKAGING_PROVENANCE_CHECKLIST.md), [operational runbook](docs/production/LOCAL_MODEL_OPERATIONAL_RUNBOOK.md) |
| Release evidence | [verification lanes](docs/production/RELEASE_VERIFICATION_LANES.md), [latency baseline](docs/production/RELEASE_LATENCY_BASELINE_HARNESS.md), [evidence packet](docs/production/RELEASE_EVIDENCE_PACKET.md), [backup/restore](docs/production/BACKUP_RESTORE_VERIFICATION.md), [rollback runbook](docs/production/LOCAL_STATE_ROLLBACK_RUNBOOK.md) |
| Ecosystem boundary | [plugin/skill boundary](docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md), [catalog](docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md), [activation grants](docs/tooling/EXTENSION_ACTIVATION_GRANTS.md), [MCP/A2A watchlist](docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md) |
| Current release | [v0.103.0 notes](docs/release_notes/v0_103_0.md), [checkpoint M169](docs/release_notes/checkpoint_m169.md) |
| Archive | [release archive](docs/archive/releases/README.md), [v0.103.0 README import](docs/archive/releases/v0_103_0/README_IMPORT.md), [v0.103.0 master plan](docs/archive/releases/v0_103_0/master_plan.md) |

Historical docs and tags are immutable audit records, not current product
claims. The historical `v2.0.0` label is not the current baseline.

## Release Discipline

Release-facing claims must match implementation and evidence. The active lanes
are documented in [Release Verification Lanes](docs/production/RELEASE_VERIFICATION_LANES.md)
and summarized by the Foundation Gate report. Release packets must distinguish
pass, fail, skipped, blocked, and accepted-failure states.

Core gate commands:

```bash
.venv/bin/python scripts/verify_all.py
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
```

## Security

Report vulnerabilities through [SECURITY.md](SECURITY.md). Maintainer triage is
documented in the [Security Triage Runbook](docs/security/SECURITY_TRIAGE_RUNBOOK.md).
Public issues and release-facing comments should use safe summaries only.

UAA preserves `PolicyEngine`, `LocalApprovalAuthority`, route side-effect
classification, OpenAPI checks, Foundation Gate checks, redaction invariants,
and no-secret-output behavior as release-blocking boundaries.
