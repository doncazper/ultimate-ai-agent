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
| Current active baseline | **v0.33.1** |
| Current milestone | **M29 hardening - Task Plan Dependency, Risk, and No-Execution Safety** |
| Development posture | Active, milestone-driven, local-first |
| Runtime posture | Contract-first, validation-first, preview-oriented |
| API boundary | FastAPI route contract with **74** OpenAPI paths |
| Production readiness | Not claimed |

v0.33.1 hardens M29 Agent Task Planning Engine as deterministic, local,
non-executing planning contracts. It strengthens dependency graph validation,
duplicate/missing step denial, self and indirect cycle detection, derived risk
checks, hidden side-effect denial, authority-boundary checks, evaluator
revalidation, and no-execution invariants. It does not execute tasks, tools,
actions, schedulers, background workers, files, memory writes, network calls,
model/provider calls, or context injection. M30-M40 remain planned/provisional.

v0.29.5 is documentation policy polish. It remains the documentation
organization cleanup baseline before the M26 and M27 implementation releases.

## Quick Links

- [Docs home](docs/README.md)
- [Documentation index](docs/DOCUMENTATION_INDEX.md)
- [Canonical document map](docs/canonical/CANONICAL_DOC_MAP.md)
- [Current roadmap](docs/canonical/09_roadmap.md)
- [API route inventory](docs/api/route_inventory.md)
- [Documentation organization policy](docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md)
- [Control Center frontend safety policy](docs/control_center/FRONTEND_SAFETY_POLICY.md)
- [M29 Agent Task Planning Engine](docs/planning/TASK_PLANNING_ENGINE.md)
- [M28 Approval Authority v2](docs/approvals/APPROVAL_AUTHORITY_V2.md)
- [M28 Action Policy](docs/approvals/ACTION_POLICY.md)
- [M27 Tool Broker v2](docs/tools/TOOL_BROKER_V2.md)
- [M26 Grounded Recall Router](docs/recall/GROUNDED_RECALL_ROUTER.md)
- [v0.33.1 release notes](docs/release_notes/v0_33_1.md)
- [v0.33.1 release packet](docs/archive/releases/v0_33_1/README_IMPORT.md)
- [v0.33.1 master plan](docs/archive/releases/v0_33_1/master_plan.md)

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
| Mobile/device clients | Planned/contract-only | Future CCC clients and device capability contracts; no native apps or sensors |
| Foundation Gate | Implemented | Release safety gate covering docs, OpenAPI, frontend, and capability boundaries |

## Safety Model

The safety posture is not a side note; it is the product architecture.

- Model output is not truth authority.
- Runtime output is not truth authority.
- Memory is recall, not authority.
- Context packs are planning artifacts, not prompt injection.
- Tool intents are not tool execution.
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
[docs/canonical/09_roadmap.md](docs/canonical/09_roadmap.md).

| Version | Milestone | Status |
|---|---|---|
| v0.30.1 | M26 hardening - Recall Source Ref / Source Kind Consistency | Implemented/released |
| v0.31.0 | M27 - Tool Broker v2 + Safe Tool Intent Contracts | Implemented/released |
| v0.31.1 | GitHub README Polish Baseline Normalization | Implemented/released docs-only |
| v0.32.0 | M28 - Approval Authority v2 + Action Policy Expansion | Implemented/released |
| v0.32.1 | M28 hardening - Evaluator Revalidation for Raw/Secret Action Inputs | Implemented/released |
| v0.33.0 | M29 - Agent Task Planning Engine | Implemented/released |
| v0.33.1 | M29 hardening - Task Plan Dependency, Risk, and No-Execution Safety | Implemented/released |
| v0.34.0 | M30 | Planned/provisional |

The roadmap intentionally separates contract planning, validation, preview,
manual local execution, and future operational authority.

## Repository Layout

```text
src/ultimate_ai_agent/     Python Agent Core contracts and validators
apps/control-center/       CCC Web React/Vite control surface
scripts/                   Verifiers, release checks, OpenAPI export, gates
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
