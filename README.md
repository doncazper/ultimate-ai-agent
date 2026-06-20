# Ultimate AI Agent

Ultimate AI Agent is a local-first, safety-first foundation for governed AI
agent work. It centers a Python Agent Core, typed contracts, redacted evidence,
approval-bound mutation paths, and verifier-backed release discipline before any
capability is allowed to become operational authority.

This repository is under active development. It is not a public release, beta,
hosted production service, broad-autonomy runtime, or unrestricted tool runner.

## Current Status

| Field | Current state |
|---|---|
| Active baseline | **v0.102.0** / `0.102.0` |
| Active program | **Operator Runtime Excellence** |
| Current lane | **Operator Runtime Excellence P2 ecosystem inspection lane through UAA-P2-051** |
| Latest repository checkpoint | **checkpoint-m168** |
| Local model lane checkpoints | **checkpoint-m166**, **checkpoint-m167** |
| API boundary | FastAPI route contract with **97** OpenAPI paths |
| Runtime posture | Contract-first, validation-first, preview-oriented |
| Production readiness | Not claimed |

The active product/package baseline is `v0.102.0` / `0.102.0`. `checkpoint-m168` is the
latest accepted repository checkpoint and repairs currentness across README,
roadmap, board, checkpoint references, product truth, and route-count
references. The M160-M167 local model lane remains scoped to local
llama.cpp/OpenWebUI readiness evidence. M166 is the exact-scope local model
production-readiness gate, and M167 adds live-evidence hardening and redacted
session/run observability without adding broader production authority.

Already-pushed tags remain immutable historical records. M150's
`v1.2.0-alpha` label is preserved as historical alpha-target context only; it
is not the active package baseline.

Current archived release packet refs:

```text
docs/archive/releases/v0_102_0/README_IMPORT.md
docs/archive/releases/v0_102_0/master_plan.md
```

## What This Repo Is

UAA is built around one principle: powerful agent behavior should be
inspectable, permissioned, reversible, and testable before it can affect real
systems.

The current implementation emphasizes:

- typed policy, approval, route, run, receipt, and evidence contracts
- FastAPI route metadata with side-effect classification
- `PolicyEngine` and `LocalApprovalAuthority` boundaries
- local model readiness through a scoped llama.cpp/OpenWebUI shell lane
- safe workspace previews, patch proposals, atomic apply, and rollback receipts
- redacted session/run observability for UAA-managed surfaces only
- release verification lanes, Foundation Gate reports, OpenAPI checks, and
  documentation integrity checks
- read-only plugin/skill ecosystem inspection, exact activation records, and an
  MCP/A2A compatibility watchlist without runtime import or execution

## What This Repo Is Not

The current baseline does not grant:

- production authority, public release, public beta, or public distribution
- broad autonomy or autonomous background sessions by default
- unrestricted shell/subprocess execution
- unrestricted network or browser automation
- connector writes outside exact reviewed scopes
- plugin runtime import or arbitrary plugin execution
- mobile control or mobile sensor runtime
- model/provider output as production authority
- raw prompt, raw response, raw provider payload, raw path, raw log, username,
  hostname, serial, environment dump, credential material, or no-secret-output
  violations in durable evidence, reports, release docs, tests, or logs

Any future expansion must name the exact scoped milestone, authority boundary,
approval model, persistence model, test plan, verifier updates, and rollback
plan.

## Architecture At A Glance

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
        +-- local model shell lane for llama.cpp/OpenWebUI
        +-- redacted observability under .uaa/
```

OpenWebUI is a shell into UAA-managed local model behavior, not the agent brain.
The Python Agent Core remains the authority boundary.

## Current Capability Map

| Area | Current state | Primary refs |
|---|---|---|
| Product truth | Evidence-backed release claims and gap matrix | [Product release-truth packet](docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md) |
| API contract | 97 OpenAPI paths, stable operation IDs, route metadata | [API boundary](docs/api/README.md), [route inventory](docs/api/route_inventory.md) |
| Security posture | Reporting, severity, triage, redaction invariants | [SECURITY.md](SECURITY.md), [triage runbook](docs/security/SECURITY_TRIAGE_RUNBOOK.md) |
| Operator shell | Gap map and product language rules for visible surfaces | [gap map](docs/control_center/OPERATOR_SHELL_GAP_MAP.md), [language rules](docs/control_center/PRODUCT_LANGUAGE_RULES.md) |
| Local model lane | Local llama.cpp/OpenWebUI readiness, E2E smoke, evidence matrix | [M167 evidence matrix](docs/production/M167_LIVE_MODEL_EVIDENCE_MATRIX.md), [E2E smoke harness](docs/production/M167_LOCAL_MODEL_E2E_SMOKE_HARNESS.md) |
| Local model operations | UAA-P0-015 provenance checklist; P0-016 hardens tuning advice; P0-017 adds safe local model operational recovery guidance | [llama-server checklist](docs/production/LLAMA_SERVER_PACKAGING_PROVENANCE_CHECKLIST.md), [operational runbook](docs/production/LOCAL_MODEL_OPERATIONAL_RUNBOOK.md) |
| Workspace workbench | Safe refs, bounded previews, approval-bound mutations, rollback receipts | [file preview policy](docs/files/LOCAL_FILE_REDACTED_PREVIEW_POLICY.md) |
| Durable runs | Append-first local run/receipt storage and lifecycle contracts | [durable run spine](docs/execution/DURABLE_RUN_SPINE.md) |
| Observability | M167 local redacted session/run logging and bounded summary APIs | [session logging](docs/observability/SESSION_LOGGING_M167.md) |
| Performance | p50/p95 release latency baseline and Foundation Gate latency integration | [release latency baseline harness](docs/production/RELEASE_LATENCY_BASELINE_HARNESS.md) |
| Release evidence | Named verification lanes, packet template, backup/restore verification, rollback guidance | [verification lanes](docs/production/RELEASE_VERIFICATION_LANES.md), [evidence packet](docs/production/RELEASE_EVIDENCE_PACKET.md), [backup/restore verification](docs/production/BACKUP_RESTORE_VERIFICATION.md), [local state rollback runbook](docs/production/LOCAL_STATE_ROLLBACK_RUNBOOK.md) |
| Ecosystem boundary | Inspectable extension catalog, activation records, MCP/A2A watchlist | [plugin/skill boundary](docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md), [catalog](docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md), [activation grants](docs/tooling/EXTENSION_ACTIVATION_GRANTS.md), [MCP/A2A watchlist](docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md) |

## Quick Start

Set up a local development environment:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
cd apps/control-center && npm install && cd ../..
```

Run the core verification lanes:

```bash
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
```

Run the aggregate checks:

```bash
make verify
make frontend-check
```

For local runtime packaging guidance, start with
[Local Runtime Packaging](docs/production/LOCAL_RUNTIME_PACKAGING.md). It is
loopback-first local readiness packaging only and does not claim public
distribution, hosted production support, or signed installer readiness.

## Documentation Map

Start here:

- [Docs home](docs/README.md)
- [Documentation index](docs/DOCUMENTATION_INDEX.md)
- [Canonical document map](docs/canonical/CANONICAL_DOC_MAP.md)
- [Current roadmap](docs/canonical/09_roadmap.md)
- [Operator Runtime Excellence roadmap](docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md)
- [Current Kanban board](docs/kanban/current_board.md)
- [Release notes for v0.102.0](docs/release_notes/v0_102_0.md)
- [Checkpoint M168 notes](docs/release_notes/checkpoint_m168.md)

Historical docs live under [docs/archive](docs/archive/README.md). They are
audit artifacts, not current implementation claims.

## Historical Roadmap Anchors

The active roadmap keeps M34-M60 labels as immutable audit anchors while the
current baseline remains v0.102.0:

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
documented in [Security Triage Runbook](docs/security/SECURITY_TRIAGE_RUNBOOK.md).
Public issues and release-facing comments should use safe summaries only.

UAA preserves `PolicyEngine`, `LocalApprovalAuthority`, route side-effect
classification, OpenAPI checks, Foundation Gate checks, redaction invariants,
and no-secret-output behavior as release-blocking boundaries.
