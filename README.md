<div align="center">

# Ultimate AI Agent

### A local-first operating environment for your work and life

**Communication, planning, relationships, knowledge, decisions, and governed
AI&mdash;designed as one coherent system.**

Built for one person first. Designed to work for anyone.

[Vision](#the-vision) &nbsp;&middot;&nbsp; [Product truth](#product-truth)
&nbsp;&middot;&nbsp; [Architecture](#architecture-at-a-glance)
&nbsp;&middot;&nbsp; [Quick start](#quick-start)

<sub>Python Agent Core &nbsp;&middot;&nbsp; FastAPI &nbsp;&middot;&nbsp; React + TypeScript
&nbsp;&middot;&nbsp; Local-first &nbsp;&middot;&nbsp; MIT licensed</sub>

</div>

---

Most software asks people to assemble their day across disconnected tools.
Ultimate AI Agent is building a different model: one calm, private environment
where first-class applications share context, canonical data, governance, and
evidence without surrendering control to an opaque agent.

UAA is designed for founders and operators first, because their work crosses
every boundary&mdash;messages, relationships, projects, decisions, research,
commitments, and execution. The same integrated model can serve a manager, a
creator, a small team, or anyone who wants technology to work as one system
instead of a pile of tabs.

> [!IMPORTANT]
> UAA is active open-source product infrastructure, not a production release or
> broad-autonomy claim. The repository distinguishes implemented, partial,
> planned, mock-only, and blocked behavior. Current truth comes from contracts,
> tests, verifiers, and redacted evidence&mdash;not screenshots or aspirations.

Current active baseline: **v0.104.0**. Package version: **0.104.0**.
Licensed under the [MIT License](LICENSE).

## The Vision

### Mission

Help people turn information and intent into clear, safe, reviewable action&mdash;
with the context they need, the controls they expect, and a durable record of
what happened.

### Product vision

UAA becomes a trusted personal operating environment: useful every day,
private by default, deeply integrated, and capable of growing from assistant to
governed operator without hiding decisions or quietly expanding its authority.

This is not a collection of thin AI wrappers. Each built-in application is
intended to be excellent on its own and materially better together:

| Application | What it owns | Current product truth |
|---|---|---|
| **Today** | Priorities, commitments, attention, and the daily operating view | Partial product spine |
| **Action Inbox** | Review, approval, rejection, deferral, and receipts for proposed changes | Proofed bounded surface; generic execution remains blocked |
| **Work Board** | Visual planning, ordering, and durable local work state | Partial backend-owned product with exact approved local mutations |
| **Messenger** | Conversations, rooms, encrypted local search, and human-commanded messaging | Partial acceptance evidence; enrolled remote runtime and persistent multi-device crypto remain incomplete |
| **CRM** | People, organizations, relationships, follow-ups, and opportunities | Partial backend-owned local product; external sync and writes remain blocked |
| **Morning Briefing** | A sourced view of what matters, what changed, and what needs attention | Partial; broader sources and background delivery remain staged |
| **Memory** | Reviewed, correctable recall with visible provenance | Proofed bounded surface; memory is recall, not truth or authority |
| **Evidence** | Decisions, receipts, provenance, replay, and rollback posture | Proofed bounded surface |

> [!NOTE]
> **Planned community direction:** Messenger can present a visible **UAA
> Community** room as an opt-in place for UAA users to meet and help one
> another. It must never silently connect, join, or expose local conversations,
> Memory, CRM, tasks, files, or agent context. Identity, moderation, encryption,
> retention, and leaving the room remain explicit product responsibilities.

The integrated advantage is the flow between those applications. A selected
message can become a relationship update, a follow-up, a board item, a calendar
proposal, and a Today commitment&mdash;reviewed as one coherent change set and
recorded as evidence. That complete flow is the product direction; only its
explicitly proofed lanes are implemented today.

```text
Signal or intent
    -> understand the context
    -> propose linked changes
    -> review exact scope
    -> approve, edit, reject, or defer
    -> commit through the owning application
    -> record receipts and evidence
    -> offer reviewed memory for the future
```

## Why UAA Is Different

| Principle | What it means in practice |
|---|---|
| **One coherent system** | Apps share typed links and one Python Agent Core while preserving one canonical owner for each task, event, relationship, message, and receipt. |
| **First-class built-ins** | Today, Messenger, Work Board, CRM, Briefing, Memory, and Evidence are product domains&mdash;not decorative dashboard widgets. |
| **Local-first by design** | Private state stays local by default. Network, connector, provider, and external-write lanes require explicit, separately governed authority. |
| **Human authority** | Models can interpret and propose. They do not silently approve their own work or turn generated output into authority. |
| **Evidence over confidence** | Important changes produce durable receipts, provenance, replay posture, and rollback or safe-disable information. |
| **One contract, every surface** | Control Center, API, CLI, and repository inspection paths converge on backend-owned truth instead of React-only product state. |

## Product North Star

![Ultimate AI Agent integrated Today workspace product concept](docs/design/control_center_north_star/renders/target-v1/01-today.png)

> **Product concept, not implementation evidence.** This image communicates the
> intended integrated experience. The current UI is not yet this complete.
> Route/API contracts, tests, verifiers, and redacted evidence remain the source
> of current product truth. See the
> [full north star](docs/portfolio/PRODUCT_NORTH_STAR.md) and
> [current status](docs/portfolio/CURRENT_STATUS.md).

## Product Truth

UAA pairs an ambitious destination with an intentionally conservative release
posture.

| Proven now | In active development | Intentionally gated |
|---|---|---|
| Python Agent Core, typed FastAPI/OpenAPI boundary, `/api/manifest`, policy and approval primitives | A polished daily loop across Today, Briefing, Work Board, CRM, Messenger, and session UX | Public release, broad autonomy, unrestricted browser/network/shell authority |
| Backend-owned decisions and durable receipts for bounded Action, Chat, Memory, and Evidence lanes | First-class app workflows, canonical cross-app ownership, backup/storage integrity, and performance | Connector writes, remote execution, hidden context injection, and generic action execution |
| Local-first evidence, redaction, idempotency, replay, and verification gates | Read-only source intelligence with provenance, freshness, and credibility posture | Provider/model authority, autonomous sends, production authority, and silent external side effects |

### What to inspect today

| Area | Current scope | Evidence |
|---|---|---|
| API boundary | Generated OpenAPI and `/api/manifest` route contract snapshot, stable operation inventory, and route classification | [API documentation](docs/api/README.md) |
| Action Inbox | Backend-owned approve/edit/reject/defer decisions, receipts, evidence refs, and one exact approved local-task capability | [state machine](docs/control_center/FCC_V1_002_ACTION_INBOX_STATE_MACHINE.md) |
| Work Board | Backend-owned Kanban read model plus exact approved local reorder, card creation, and task-record persistence | [surface gap map](docs/control_center/OPERATOR_SHELL_GAP_MAP.md) |
| Messenger | Exact bounded local Matrix lanes, synthetic desktop coverage, and a finite partial acceptance packet | [acceptance packet](docs/connectors/MESSENGER_MATRIX_ACCEPTANCE_PACKET.md) |
| CRM | Local read models, CLI inspection, storage posture, import/export preview, and exact local mutation receipts | [CRM M2](docs/control_center/CRM_LOCAL_COMMAND_CENTER_M2.md) |
| Memory and Evidence | Reviewed recall records, read-only indexes, proposal-only context packs, and a safe-ref evidence timeline | [memory spine](docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_V1.md) |

For the complete implemented/partial/planned/blocked ledger, read the
[current status](docs/portfolio/CURRENT_STATUS.md),
[release truth packet](docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md), and
[operator shell gap map](docs/control_center/OPERATOR_SHELL_GAP_MAP.md).

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
| API boundary | FastAPI route contract with generated OpenAPI and manifest route-operation inventory |
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

### First-Class macOS App

The private/local macOS distribution lane produces a self-contained
`Ultimate AI Agent.app` plus a checkout-independent `uaa` command. The app and
CLI share launch, doctor, status, update, stop, and rollback behavior; the
installed runtime does not require a repository checkout, `.venv`, Node, npm,
or Vite.

```bash
packaging/macos/install.sh \
  --local-archive BUILD_DIR/uaa-macos-arm64.tar.gz \
  --local-descriptor BUILD_DIR/uaa-macos-arm64.release.json

uaa doctor
uaa launch
```

Remote private installation becomes active when an eligible post-installer tag
publishes the long-lived bootstrap and app release assets. Developer ID signing
and notarization remain blocked on Apple credentials; verified local builds are
ad-hoc signed and are not a public-distribution claim. See
[the macOS installer guide](docs/production/MACOS_FIRST_CLASS_INSTALLER.md).

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

Production Control Center builds use strict backend mode and fail visibly when
the backend is unavailable; they do not substitute mock panel data. The local
launcher transfers its bearer through a one-use URL fragment that is consumed
into memory and removed from browser history. `VITE_UAA_LOCAL_API_BEARER` is no
longer supported because Vite values are build-visible.

### Inspect The Founder Loop

```bash
.venv/bin/python scripts/dev/uaa_founder_loop.py inspect
```

### Back Up And Restore Founder Loop State

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_founder_loop_recovery.py backup \
  --state-dir STATE_DIR --backup-dir BACKUP_DIR --confirm-offline
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_founder_loop_recovery.py verify \
  --backup-dir BACKUP_DIR
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_founder_loop_recovery.py restore \
  --backup-dir BACKUP_DIR --target-state-dir RESTORE_DIR \
  --confirm-offline-restore
```

The recovery lane uses real SQLite and JSONL state, verifies integrity before
restore, checks available space, and publishes through an atomic staging path.
See `docs/verification/PRODUCT_HARDENING_EVIDENCE_GATE.md` for limitations and
the independent review gate.

### Inspect Build Identity

```bash
PYTHONPATH=src .venv/bin/python scripts/inspect_build_identity.py
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
make verify-affected
make verify-value-audit
make verify-dev-fast
make test-sharded
make test-sharded-profile
make verify-dev-sharded
make frontend-check
```

`make verify` is the release-grade local gate. It runs Ruff, the complete
timing-balanced pytest inventory, static verification, gate architecture, and a
serialized report-only Foundation Gate. `make test-serial` remains available
for order-sensitive diagnostics. `make verify-fast` runs a deterministic,
fail-closed changed-path selection for the smallest useful local feedback;
`make verify-affected` adds the affected boundary verifiers. Both are advisory
and unknown or verification-topology paths fall back to the full local/dev
gate. They never replace merge or release verification.
`make verify-dev-fast` runs the four pre-gate phases concurrently, then
serializes Foundation Gate with `--no-write-latest`. `VERIFY_DEV_FAST_JOBS`
bounds top-level phase fanout and `PYTEST_SHARD_WORKERS` independently bounds
the pytest subprocess pool. This is local verification evidence, not a
release-readiness claim by itself. Hosted CI proves pytest equivalence through
eight isolated, timing-balanced file shards plus one stable aggregate `pytest`
check.

`make test` and `make test-sharded` use the same canonical local pytest lane.
It uses
`scripts/verification/run_pytest_shards.py` with `PYTEST_SHARDS` (eight local
shards and workers by default), stores
inspectable shard logs and isolated pytest temp dirs under ignored `/tmp`
paths, and writes local file timing data to `PYTEST_SHARD_TIMINGS_JSON`. The
runner starts with the tracked, repo-relative advisory timing seed, overlays a
newer local timing file when present, and greedily balances files by prior
duration. Missing files receive a conservative p90 estimate instead of being
dropped or disabling timing data. Tests that consume the real session-scoped
Foundation Gate fixture remain together on one process so the full gate is
evaluated once per complete shard run. The timing seed is scheduling input
only: it is not cached test, authority, or release evidence.
Normal runs do not regenerate timing data. Use `make test-sharded-profile` for
an explicit complete green timing refresh; failed runs never replace the local
profile.

The canonical local lane has a 110-second stretch goal, a 125-second performance
budget, and a 180-second hard wall-clock limit. The eight-worker default bounds
parallel contention on the canonical macOS development host; local timing
profiles should be refreshed before changing that topology. Crossing the stretch goal emits
an optimization notice. Crossing the performance budget emits a warning and
marks the local `PYTEST_PERFORMANCE_REPORT` as requiring refactoring. Crossing
the hard limit terminates every active shard process group, prevents pending
shards from starting, writes a content-free report of shard timings and ranked
repo-relative test-file candidates, and exits with code 124. Override variables
exist for controlled diagnostics, but raising the checked-in limits is not a
substitute for fixing slow fixtures, repeated scans, or unbalanced tests.

`make verify-dev-sharded` runs the same local/dev
composition through `scripts/verification/run_dev_fast_gate.py`: `ruff`,
sharded pytest, static verification, and gate architecture run in bounded local
fanout, then Foundation Gate runs serialized in report-only mode with
`--no-write-latest`. The runner captures per-phase logs under ignored `/tmp`
paths, writes a timing summary, prints concise pass/fail phase summaries, and
prints detailed log tails when a phase fails. This remains local pre-review
feedback. Hosted CI requires every shard through the aggregate `pytest` check;
every discovered test file remains assigned exactly once.

The sharded lane parallelizes the same default-safe contract test posture. It
does not opt into live GGUF search or acquisition, local model root
enumeration, model loading, model benchmarking, llama.cpp startup, OpenWebUI
startup, provider live-network tests, or model-router sweeps. Shard
subprocesses strip known live/model-heavy opt-in environment variables before
pytest starts, so optional live tests remain skipped by default.

The fast and affected lanes do not cache pass results. They derive changed
paths from Git, normalize and sort them, and use a fixed command registry.
Unknown paths fail closed to `make verify-dev-sharded`; direct `--path` values
are additive and cannot hide Git state.
See [Fast local verification](docs/verification/FAST_LOCAL_VERIFICATION.md).

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
| [docs/product/UAA_SOCIAL_MEDIA_INTELLIGENCE_PRODUCT_CONTRACT.md](docs/product/UAA_SOCIAL_MEDIA_INTELLIGENCE_PRODUCT_CONTRACT.md) | Planned read-only Social Media Intelligence product and ownership contract |
| [docs/prompts/implement_social_media_intelligence_after_foundation_gates.prompt.md](docs/prompts/implement_social_media_intelligence_after_foundation_gates.prompt.md) | Deferred execution prompt gated on Work Board, CRM, and Communications completion |
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
- **Social Media Intelligence**: deferred read-only creator command view, eligible
  only after Work Board/Kanban, first-class CRM, and Communications/Messenger
  have accepted completion evidence.
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

Ultimate AI Agent is licensed under the [MIT License](LICENSE).
