# Ultimate AI Agent

A local-first, safety-first AI agent architecture for building governed AI
systems around a Python Agent Core, typed contracts, preview-oriented control
surfaces, and milestone-gated safety reviews.

Ultimate AI Agent is under active development. It is designed to make powerful
agent behavior inspectable, permissioned, reversible, and testable before it is
allowed to become operational authority.

## Status

| Field | Current state |
|---|---|
| Current active baseline | **v0.41.0** |
| Current milestone | **M37 - Review Approval Capture, Review-Only Persistence** |
| Development posture | Active, milestone-driven, local-first |
| Runtime posture | Contract-first, validation-first, preview-oriented |
| API boundary | FastAPI route contract with **75** OpenAPI paths |
| Production readiness | Not claimed |

v0.41.0 implements M37 Review Approval Capture, Review-Only Persistence. It
adds safe review-only approval and denial capture for exact redacted file
review packets, safe-ref-only persistence, idempotency/replay protection, one
backend capture route, Control Center review-only capture controls, tests,
static verification, documentation-integrity checks, and Foundation Gate
coverage. It adds no raw file reads, raw file output/storage, full-file reads,
unredacted preview, context proposal, context injection, memory writes, export,
execution controls, dependencies, M38 work, or production authority.

v0.29.5 is documentation policy polish. It remains the documentation
organization cleanup baseline before the M26 and M27 implementation releases.

## Quick Links

- [Docs home](docs/README.md)
- [Documentation index](docs/DOCUMENTATION_INDEX.md)
- [Canonical document map](docs/canonical/CANONICAL_DOC_MAP.md)
- [Current roadmap](docs/canonical/09_roadmap.md)
- [M34-M60 roadmap supersession](docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md)
- [M34 Broader File Capability Review](docs/files/BROADER_FILE_CAPABILITY_REVIEW.md)
- [File capability boundary matrix](docs/files/FILE_CAPABILITY_BOUNDARY_MATRIX.md)
- [File capability risk register](docs/files/FILE_CAPABILITY_RISK_REGISTER.md)
- [M35 file review workflow readiness](docs/files/M35_SAFE_FILE_REVIEW_WORKFLOW_READINESS.md)
- [M35 Safe File Review Workflow](docs/files/SAFE_FILE_REVIEW_WORKFLOW.md)
- [M35 File Review Packet Contract](docs/files/FILE_REVIEW_PACKET_CONTRACT.md)
- [M35 File Review User Approval Gate](docs/files/FILE_REVIEW_USER_APPROVAL_GATE.md)
- [M35 File Review Authority Boundary](docs/files/FILE_REVIEW_AUTHORITY_BOUNDARY.md)
- [M36 CCC File Review Surface](docs/control_center/FILE_REVIEW_SURFACE.md)
- [M36 File Review Review-Only Policy](docs/control_center/FILE_REVIEW_REVIEW_ONLY_POLICY.md)
- [M36 File Review Mock Data Policy](docs/control_center/FILE_REVIEW_MOCK_DATA_POLICY.md)
- [M36 File Review Binding Display Policy](docs/control_center/FILE_REVIEW_BINDING_DISPLAY_POLICY.md)
- [M37 File Review Approval Capture](docs/files/FILE_REVIEW_APPROVAL_CAPTURE.md)
- [M37 File Review Approval Persistence](docs/files/FILE_REVIEW_APPROVAL_PERSISTENCE.md)
- [M37 File Review Approval Authority Boundary](docs/files/FILE_REVIEW_APPROVAL_AUTHORITY_BOUNDARY.md)
- [M37 File Review Approval API](docs/files/FILE_REVIEW_APPROVAL_API.md)
- [API route inventory](docs/api/route_inventory.md)
- [Documentation organization policy](docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md)
- [Control Center frontend safety policy](docs/control_center/FRONTEND_SAFETY_POLICY.md)
- [Local developer launcher](docs/developer/LOCAL_LAUNCHER.md)
- [M31 Tool Runtime Adapter](docs/tools/TOOL_RUNTIME_ADAPTER.md)
- [M31 No-Op Tool Runtime](docs/tools/NOOP_TOOL_RUNTIME.md)
- [M32 Filesystem Metadata Tool](docs/tools/FILESYSTEM_METADATA_TOOL.md)
- [M32 Filesystem Metadata Path Policy](docs/tools/FILESYSTEM_METADATA_PATH_POLICY.md)
- [M33 Redacted File Preview Tool](docs/tools/REDACTED_FILE_PREVIEW_TOOL.md)
- [M33 Redacted File Preview Policy](docs/tools/REDACTED_FILE_PREVIEW_POLICY.md)
- [M30 Multi-Step Execution Framework](docs/execution/MULTI_STEP_EXECUTION_FRAMEWORK.md)
- [M29 Agent Task Planning Engine](docs/planning/TASK_PLANNING_ENGINE.md)
- [M28 Approval Authority v2](docs/approvals/APPROVAL_AUTHORITY_V2.md)
- [M28 Action Policy](docs/approvals/ACTION_POLICY.md)
- [M27 Tool Broker v2](docs/tools/TOOL_BROKER_V2.md)
- [M26 Grounded Recall Router](docs/recall/GROUNDED_RECALL_ROUTER.md)
- [v0.41.0 release notes](docs/release_notes/v0_41_0.md)
- [v0.41.0 release packet](docs/archive/releases/v0_41_0/README_IMPORT.md)
- [v0.41.0 master plan](docs/archive/releases/v0_41_0/master_plan.md)

## What This Project Is

Ultimate AI Agent is a foundation workspace for a governed AI agent system. The
repo favors typed contracts, local validation, deterministic tests, static
verifiers, and release gates over early runtime power.

Core themes:

- **Python Agent Core is the brain.** Policy, contracts, validation, approvals,
  redaction, memory governance, truth decisions, recall planning, and tool
  intent decisions belong in the core.
- **Control Center / CCC is the governance client family.** CCC Web exists as a
  local React/Vite control surface for safe summaries, status, and previews.
  Future CCC iOS, Android, and macOS clients are planned, not implemented.
- **OpenWebUI is the preferred conversational shell direction.** The current
  repo contains contract and strategy docs, not an operational OpenWebUI
  integration.
- **Memory is recall, not authority.** Memory can help plan recall context, but
  governed source refs outrank memory for truth.
- **Tool intents are contracts, not execution.** M27 validates tool intent
  metadata and can allow metadata-only preview decisions with
  `execution_performed=False`.
- **Approval decisions are policy decisions, not action execution.** M28
  validates action intent, grant, risk, and scope boundaries with
  `execution_authorized=False` and `execution_performed=False`.
- **Tool runtime is allowlist-only.** M33 permits exactly three governed runtime
  tools: deterministic no-op, safe local filesystem metadata, and bounded
  redacted file preview. The preview tool returns redacted preview output only;
  it cannot return raw content, full files, hashes, listings, or mutate files.

## What This Project Is Not

This repo is deliberately not an unrestricted autonomous executor.

It does not currently provide:

- production agent authority
- general cloud/provider model execution
- backend tool execution routes
- shell, subprocess, browser, mobile, remote, or plugin execution
- context injection into a model, runtime, OpenWebUI, tool, or agent loop
- vector search, embeddings, semantic search, or RAG ingestion
- web search or external retrieval
- unrestricted memory writes or raw prompt/file/transcript display
- implemented native iOS, Android, or macOS apps

Future milestones may expand capability, but only through reviewed, documented,
release-gated patches.

## Architecture Overview

```text
Ultimate AI Agent
  Python Agent Core
    Runtime contracts and bounded local smoke paths
    Memory: recall, not authority
    Truth/Evidence: validation over provided refs
    Recall/Context Packs: safe plans, not injection
    Tool Intent Contracts: preview/validation, not execution
    Tool Runtime Adapter: no-op, metadata-only filesystem lookup, redacted file preview
  Control Center / CCC Web
    Local governance and preview surfaces
  OpenWebUI Strategy
    Preferred conversational shell direction, contract-only today
  Foundation Gate + Verifiers
    Tests, docs integrity, OpenAPI checks, frontend checks, safety scans
```

The project advances by small milestones. Each milestone states what it enables,
what it blocks, which docs are active, and which tests/verifiers protect the
boundary.

## Capability Map

| Layer | Current status | Notes |
|---|---|---|
| Python Agent Core | Implemented foundation | Contract-first core under `src/ultimate_ai_agent/` |
| FastAPI backend | Implemented validation/metadata API | OpenAPI path count remains 74 |
| CCC Web Control Center | Implemented preview/read-only local shell | React/Vite app under `apps/control-center/` |
| OpenWebUI bridge | Contract/planning only | Preferred shell strategy; no live integration |
| Local model runtime | Bounded/manual only | M23 fixed-prompt, loopback-only, approval-gated CLI path; model output is non-authoritative |
| Memory | Implemented governed local foundation | Reviewed/source-linked recall records; no automatic writes |
| Truth/evidence | Implemented M25 contracts | Deterministic validation over provided refs; no external lookup |
| Recall/context packs | Implemented M26 contracts | Safe summaries and refs only; source_ref/source_kind consistency enforced |
| Tool Broker v2 | Implemented M27 contracts | Safe intent validation and metadata preview only; no execution |
| Approval Authority v2 | Implemented M28 contracts | Action policy decisions only; no execution authority |
| Tool Runtime Adapter | Implemented M33 allowlist-only | `tool:no_op.v1`, `tool:filesystem_metadata.v1`, and `tool:filesystem.redacted_preview.v1`; arbitrary/effectful tools blocked |
| Mobile/device clients | Planned/contract-only | Future CCC clients and device capability contracts; no native apps or sensors |
| Foundation Gate | Implemented | Release safety gate covering docs, OpenAPI, frontend, and capability boundaries |

## Safety Model

The safety posture is not a side note; it is the product architecture.

- Model output is not truth authority.
- Runtime output is not truth authority.
- Memory is recall, not authority.
- Context packs are planning artifacts, not prompt injection.
- Tool intents are not tool execution.
- M33 tool runtime is limited to deterministic no-op, safe local filesystem
  metadata, and bounded redacted file preview under server-owned safe roots.
- Redacted file previews are not raw file reads, full-file reads, or context
  injection.
- Approval decisions are not action execution.
- Approval refs are identifiers, not authority.
- `approval_test_*` refs are test-only and not runtime authority.
- Local/dev mode is not a security bypass.
- Raw prompts, raw files, raw transcripts, raw model outputs, and secret-like
  values are blocked or redacted unless a reviewed contract explicitly allows a
  safe summary/ref form.
- Foundation Gate, documentation integrity checks, OpenAPI checks, frontend
  checks, and static safety verifiers are part of the architecture.

## Getting Started Locally

Create a local Python environment and install the project with development
extras:

```bash
python3 -m venv .venv
source .venv/bin/activate
.venv/bin/python -m pip install -e ".[dev]"
```

Run the standard backend and repository checks:

```bash
make doctor
make test
make verify
```

The equivalent explicit commands are:

```bash
PYTHONPATH=src .venv/bin/python -m pytest
.venv/bin/python scripts/verify_current_baseline.py
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_skill_package_security_rule.py
.venv/bin/python scripts/verify_control_center_frontend.py
.venv/bin/python scripts/verify_all.py
.venv/bin/python scripts/run_foundation_gate.py
.venv/bin/python scripts/verify_openapi_contract.py
.venv/bin/python -m ruff check .
```

For the Control Center frontend:

```bash
cd apps/control-center
npm install
npm run typecheck
npm run lint
npm run test -- --run
npm run build
```

Or from the repo root:

```bash
make frontend-check
```

## Local Developer Launcher

For day-to-day prototype testing, use the repo-local launcher:

```bash
./scripts/dev/uaa doctor
./scripts/dev/uaa start
./scripts/dev/uaa ui
./scripts/dev/uaa status
./scripts/dev/uaa logs
./scripts/dev/uaa stop
```

It starts only the local FastAPI backend on `127.0.0.1:8000` and the Control
Center Vite dev server on `127.0.0.1:5173`. PID and log files stay under
ignored `.uaa/dev/` launcher state.

Optional shell convenience:

```bash
mkdir -p ~/.local/bin
ln -s "$(pwd)/scripts/dev/uaa" ~/.local/bin/uaa
```

Then run `uaa doctor`, `uaa start`, and `uaa ui`.

For a clickable macOS launcher:

```bash
.venv/bin/python scripts/dev/create_macos_launcher.py --target repo
```

Read the full launcher guide at
[docs/developer/LOCAL_LAUNCHER.md](docs/developer/LOCAL_LAUNCHER.md).

## Control Center

CCC Web is the current TypeScript Control Center surface. It is local,
read-only/preview-oriented, and visibly non-authoritative where mock fallback
data is used.

It may show status, route inventory, runtime readiness, approval summaries,
receipts, events, evidence refs, file refs, memory refs, local runtime status,
and safe action previews. It must not grant approvals, run tools, execute
runtimes, enable plugins, call providers, access browser profiles, use mobile
sensors, or become production authority.

Read more:

- [Control Center contract](docs/control_center/CONTROL_CENTER_CONTRACT.md)
- [Frontend safety policy](docs/control_center/FRONTEND_SAFETY_POLICY.md)
- [Control Center frontend routes](docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md)

## Roadmap Snapshot

The canonical roadmap source of truth is
[docs/canonical/09_roadmap.md](docs/canonical/09_roadmap.md). The active
post-M33 supersession is
[docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md](docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md).

| Version | Milestone | Status |
|---|---|---|
| v0.30.1 | M26 hardening - Recall Source Ref / Source Kind Consistency | Implemented/released |
| v0.31.0 | M27 - Tool Broker v2 + Safe Tool Intent Contracts | Implemented/released |
| v0.31.1 | GitHub README Polish Baseline Normalization | Implemented/released docs-only |
| v0.32.0 | M28 - Approval Authority v2 + Action Policy Expansion | Implemented/released |
| v0.32.1 | M28 hardening - Evaluator Revalidation for Raw/Secret Action Inputs | Implemented/released |
| v0.33.0 | M29 - Agent Task Planning Engine | Implemented/released |
| v0.33.1 | M29 hardening - Task Plan Dependency, Risk, and No-Execution Safety | Implemented/released |
| v0.34.0 | M30 - Multi-Step Execution Framework | Implemented/released |
| v0.34.1 | M30 hardening - Execution State Machine, Replay, and No-Side-Effect Safety | Implemented/released |
| v0.35.0 | M31 - Real Tool Runtime Adapter, Single Safe No-Op Tool | Implemented/released |
| v0.35.1 | M31 hardening - No-Op Tool Runtime Adapter Safety | Implemented/released |
| v0.36.0 | M32 - Safe Local Filesystem Metadata Tool | Implemented/released |
| v0.36.1 | M32 hardening - Filesystem Metadata Path Safety | Implemented/released |
| v0.37.0 | M33 - First Safe Local File Read Proposal, Redacted Preview Only | Implemented/released |
| v0.37.1 | M33 hardening - Redacted File Preview Safety | Implemented/released |
| v0.37.2 | Local Developer Launcher + Desktop Shortcut | Implemented/released tooling-only |
| v0.37.3 | Roadmap Label Alignment + Documentation Integrity Guard | Implemented/released docs/verifier-only |
| v0.37.4 | Roadmap Supersession Through M60 + Documentation Integrity Guard | Implemented/released docs/verifier-only |
| v0.38.0 | M34 - Broader File Capability Review | Implemented/released planning/docs/verifier-only |
| v0.38.1 | M34 hardening - File Capability Review Boundary Clarity | Pushed, reviewed Yellow; superseded by v0.38.2 |
| v0.38.2 | M34 hardening - Current Baseline Label + Documentation Integrity Repair | Implemented/released docs/verifier-only |
| v0.39.0 | M35 - Safe File Review Workflow Contracts | Implemented/released contract-only |
| v0.39.1 | M35 hardening - File Review Exact File/Path Binding | Implemented/released hardening |
| v0.40.0 | M36 - CCC File Review Surface, Review-Only | Implemented/released frontend-only |
| v0.40.1 | M36 hardening - CCC File Review Surface Read-Only Safety | Implemented/released hardening |
| v0.41.0 | M37 - Review Approval Capture, Review-Only Persistence | Implemented/released |
| v0.42.0 | M38 - Safe Context Proposal From Approved Review | Planned/provisional |
| v0.43.0 | M39 - CCC Context Proposal Surface | Planned/provisional |
| v0.44.0 | M40 - Context Handoff Approval, No Injection | Planned/provisional |
| v0.45.0 | M41 - Local Prototype Safety Freeze | Planned/provisional |
| v0.46.0 | M42 - Mobile Companion Product Contract Refresh | Planned/provisional |
| v0.47.0 | M43 - Mobile API Boundary, Read-Only | Planned/provisional |
| v0.48.0 | M44 - CCC iOS Skeleton, No Authority | Planned/provisional |
| v0.49.0 | M45 - CCC iOS Local Read-Only Connection | Planned/provisional |
| v0.50.0 | M46 - iOS Review/Receipt Read-Only Surfaces | Planned/provisional |
| v0.51.0 | M47 - TestFlight Pipeline, Internal Only | Planned/provisional |
| v0.52.0 | M48 - First Internal TestFlight Build | Planned/provisional |
| v0.53.0 | M49 - Mobile Review Approval Capture | Planned/provisional |
| v0.54.0 | M50 - Mobile Approval Audit Hardening | Planned/provisional |
| v0.55.0 | M51 - OpenWebUI Bridge Adapter Pilot | Planned/provisional |
| v0.56.0 | M52 - OpenWebUI Safe Conversation Surface | Planned/provisional |
| v0.57.0 | M53 - Controlled Tool Expansion Review | Planned/provisional |
| v0.58.0 | M54 - Safe Media Metadata Inspector | Planned/provisional |
| v0.59.0 | M55 - Redacted Observability Export | Planned/provisional |
| v0.60.0 | M56 - Agent Eval Regression Harness | Planned/provisional |
| v0.61.0 | M57 - Runtime Sandbox Architecture Review | Planned/provisional |
| v0.62.0 | M58 - Dry-Run Execution Audit Harness | Planned/provisional |
| v0.63.0 | M59 - Public GitHub Readiness | Planned/provisional |
| v0.64.0 | M60 - Local Developer Beta Freeze | Planned/provisional |

The roadmap intentionally separates contract planning, validation, preview,
manual local execution, and future operational authority.

## Repository Layout

```text
src/ultimate_ai_agent/     Python Agent Core contracts and validators
apps/control-center/       CCC Web React/Vite control surface
scripts/                   Verifiers, release checks, OpenAPI export, gates
scripts/dev/               Local developer launcher tooling
tests/                     Unit, contract, safety, and Foundation Gate tests
docs/                      Active docs, canonical maps, release notes, archive
VERSION.md                 Current active baseline summary
AGENTS.md                  Workspace rules and milestone safety boundaries
Makefile                   Repo-local verification commands
```

Historical release artifacts live under `docs/archive/`. The root directory is
kept minimal and current by policy.

## Verification Philosophy

Ultimate AI Agent treats verification as a first-class design surface.

Release work is expected to preserve:

- deterministic Python tests
- OpenAPI route-contract stability
- static safety scans for forbidden capability drift
- documentation integrity checks
- frontend typecheck/lint/test/build coverage
- Foundation Gate criteria for milestone boundaries
- clean version, tag, and release-packet alignment

The main verification entrypoints are:

- `make test`
- `make verify`
- `make frontend-check`
- `.venv/bin/python scripts/run_foundation_gate.py`
- `.venv/bin/python scripts/verify_openapi_contract.py`

## Documentation

The root README is an entrypoint, not the full documentation site.

- Start with [docs/README.md](docs/README.md).
- Use [docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md) for the full
  active documentation map.
- Use [docs/canonical/CANONICAL_DOC_MAP.md](docs/canonical/CANONICAL_DOC_MAP.md)
  to find source-of-truth documents by system.
- Use [docs/canonical/09_roadmap.md](docs/canonical/09_roadmap.md) for current
  sequencing.
- Use [docs/archive/README.md](docs/archive/README.md) for historical context.

Active docs may claim the current active baseline. Archived docs are audit
records and must not be treated as current source of truth.

## Development Posture

When changing this repo:

- keep milestone changes small and release-gated
- preserve the current safety boundary unless a prompt explicitly changes it
- add tests or verifier coverage for safety bugs
- do not commit secrets, credentials, raw private data, or generated artifacts
- keep root docs current and historical docs clearly archived
- use `.venv/bin/python`, not bare `python`, for repo verification commands

## License

License: not yet declared.
