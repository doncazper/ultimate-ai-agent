# Ultimate AI Agent

Ultimate AI Agent (UAA) is a local-first foundation for governed AI agent work.
It puts a Python Agent Core, typed contracts, approvals, redacted evidence,
rollback paths, and verifier-backed release discipline in front of any
capability that could affect real systems.

This repository is under active development. It is not a public release, public
beta, hosted production service, broad-autonomy runtime, or unrestricted tool
runner.

## Current Status

| Field | Current state |
|---|---|
| Active baseline | **v0.102.3** / `0.102.3` |
| Active program | **Operator Runtime Excellence** |
| Current lane | **FCC-V1-002 Complete: Action Inbox Backend State Machine; FCC-V1-003 Next: Founder Loop V1 Vertical Slice; UAA-P1-087.2 Private UI Testing Deferred** |
| Product wedge | **Founder Command Center / macOS-of-agents strategy spine** |
| Founder Loop V1 conveyor | **FCC-V1-000 through FCC-V1-002 complete; FCC-V1-003 through FCC-V1-007 planned: vertical loop, Chat receipts/handoff, Memory decisions, Evidence productization, and proof-lane promotion** |
| Latest repository checkpoint | **checkpoint-m168** |
| Local model lane checkpoints | **checkpoint-m166**, **checkpoint-m167** |
| API boundary | FastAPI route contract with **117** OpenAPI paths |
| Runtime posture | Contract-first, validation-first, preview-oriented |
| Production readiness | Not claimed |

The active product/package baseline is `v0.102.3` / `0.102.3`.
`checkpoint-m168` is the latest accepted repository checkpoint and repairs
currentness across README, roadmap, board, checkpoint references, product truth,
and route-count references. The M160-M167 local model lane remains scoped to
local llama.cpp/OpenWebUI readiness evidence. M166 is the exact-scope local
model production-readiness gate, and M167 adds live-evidence hardening and
redacted session/run observability without adding broader production authority.
UAA-P1-065 completes the Founder Command Center review cleanup without adding
runtime authority. UAA-P1-067 completes the Today-spine, memory-first
beta-readiness planning/currentness pass and adds the milestone conveyor
without adding runtime authority. UAA-P1-068 completes the Today Product Spine
Contract on the existing Today summary route with a schema, verifier, focused
tests, and read-only Today render. UAA-P1-069 completes the Evidence History
Grammar contract so Evidence answers what was proposed, approved, happened,
changed, can be undone, is stale, and remains blocked with safe refs and
redacted summaries only. UAA-P1-070 Memory Source And Provenance Model is
complete with core memory provenance contracts, safe source refs,
review-required posture, and denied authority flags. UAA-P1-071 Memory Review
Decision Capture is complete with review-only decision metadata, blocked
write/delete/export posture, and read-only Control Center visibility. UAA-P1-072
Business Memory And Memory Quality Controls is complete with CRM-lite candidate
kinds, duplicate/conflict/stale/low-confidence/source/evidence quality posture,
safe-ref Today/Action/Evidence/Weekly Review binding, and read-only Control
Center visibility. UAA-P1-073 Plans To Reviewable Action Envelopes is complete
with approve/edit/reject/defer-ready envelope metadata, exact scope refs,
side-effect/risk/approval posture, expected receipt refs, rollback and
safe-disable refs, blocked authority states, and read-only Control Center
visibility. UAA-P1-074 Chat Local Operator Surface is complete with a
first-party local operator turn truth surface, model/runtime/auth/tool-denial
metadata, safe evidence refs, proposal handoff refs, blocked authority states,
and read-only Control Center visibility. UAA-P1-075 Governed Code Workbench V1
is complete with repo-local proposal scope, safe diff summary refs, validation
plan refs, expected apply and rollback receipt refs, Evidence Timeline binding,
blocked apply authority, and read-only Control Center metadata shape.
UAA-P1-076 Cross-Surface Memory Intake is complete with review-only memory
intake proposals from Today, Chat, Plans, Actions, Evidence, local coding, and
manual external-assistant review imports; memory writes, automatic recall,
context injection, provider calls, account fetch, browser import, shell-history
import, and source import remain blocked. UAA-P1-077 Memory-To-Loop Binding is
complete with read-only loop refs across Today, Action Inbox, Evidence
Timeline, Memory Review, and Weekly CEO Review; accepted recall remains
display-only, memory-derived actions remain approval-bound proposals, and
memory writes, context injection, execution, connector writes, account sync,
public beta, distribution, and production authority remain blocked. UAA-P1-078
Private Beta-Readiness Gate is complete with a read-only local/private
beta-test readiness evidence gate across Today, Morning Briefing, Action
Inbox, Memory Review, Evidence Timeline, Chat/Plans Handoff, Governed Code,
and CRM-lite follow-ups. UAA-P1-079 User Intent Understanding V1 is complete
with reviewable intent proposals, confidence, source refs, evidence refs,
ambiguity posture, and ask/act/defer routing; low-confidence or conflicting
intent asks the user rather than acting. UAA-P1-080 API Route Classification
And Public/Protected Inventory is complete with typed route classifications in
`/api/manifest`, a frozen 117-route inventory fixture, route-status manifest
alignment, Control Center API Routes visibility, and focused verifier/tests.
UAA-P1-081 Centralized FastAPI Security Headers is complete with centralized
response headers, HTTPS-only HSTS behavior, no CORS/auth/rate-limit authority,
manifest capability posture, and focused verifier/tests. UAA-P1-082 Explicit
Loopback CORS Allowlist is complete with exact local Control Center dev/preview
origins, no wildcard CORS, no CORS credentials, no auth claim, manifest
capability posture, and focused verifier/tests. UAA-P1-083 Local Bearer Or
Session Gate For Sensitive Routes is complete with a configured local bearer
gate for non-public route classifications, public metadata routes left open,
no enterprise/OAuth/password-flow claim, and focused verifier/tests. UAA-P1-084
Mutating Route Idempotency Enforcement Audit is complete with a runtime
idempotency header gate for `mutating_requires_authority` routes, no durable
dedupe or exactly-once execution claim, and focused verifier/tests. UAA-P1-085
Targeted Rate Limits For Expensive And Sensitive Routes is complete with
targeted local fixed-window rate limits for model/chat, task-decomposition,
action preview/proposal, and expensive validation/local-model paths, no auth
or distributed quota claim, no dependency addition, and focused
verifier/tests. UAA-P1-086 API Boundary Enforcement Tests is complete with
OpenAPI, `/api/manifest`, route inventory fixture, route-status manifest,
protected-route, idempotency, header, CORS, and rate-limit enforcement checks
without adding routes, middleware, runtime authority, public beta, or
production authority. UAA-P1-087.1 Local Launcher Dual-Surface Boot Readiness
is complete with `./scripts/dev/uaa trial-boot`, macOS `.command` binding,
Control Center-first boot, secondary OpenWebUI blocked-state guidance,
backend/frontend/OpenWebUI status, stop coverage, and safe launcher log refs.
UAA-P1-087.2a Private Trial Packet And UI Tuning Surface is complete with a
safe-ref-only trial packet, read-only Control Center `/private-trial` surface,
manual smoke checklist refs, friction refs, UI/copy task refs, and blocked
authority refs. UAA-P1-087.2b Private Trial Findings Capture And Acceptance
Ledger is complete with a safe-ref-only acceptance ledger, manual smoke step
refs, pending operator review findings, acceptance question refs, tuning
decision refs, and read-only Control Center visibility. UAA-P1-087.2c Private
Trial Manual Review Scaffold is complete with unanswered pending answer refs,
missing implementation refs, deferred decision refs, and read-only Control
Center visibility without accepted or revised manual-review answers. These
slices install no
packages, pull no images, add no backend route, and add no runtime authority.
Full UAA-P1-087.2 in-person private UI functional tuning remains planned but
deferred until more Founder Loop implementation exists and accepted or revised
local/private findings can be recorded. UAA-P1-087.3 native SwiftUI boot
cockpit planning/source-only scaffold stays deferred behind full UAA-P1-087.2.
FCC-V1-000 Control Center Release Surface Manifest is complete with a
route-status schema, manifest, verifier, focused tests, and conservative
`ship`/`partial`/`blocked`/`experimental` truth for every visible Control
Center route. It adds no backend route or runtime authority and does not answer
deferred UAA-P1-087.2 manual-review questions. FCC-V1-001 API Perimeter For
Real Mutations is complete as contract and verifier coverage, with duplicate
replay runtime still blocked until route-owner receipt storage exists outside
routes that implement their own receipt-backed replay.
FCC-V1-002 Action Inbox Backend State Machine is complete for backend-owned
approve/edit/reject/defer decision state, exact approval validation where
required, idempotency replay/conflict handling, local receipt refs, and Control
Center receipt visibility. It does not execute approved actions or grant
connector, shell/subprocess, provider/model, memory-write, public beta, or
production authority.
The planned Founder Loop V1 productization conveyor is recorded in
`docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md` as `FCC-V1-000` through
`FCC-V1-007`: completed Control Center release surface manifest, API perimeter
for real mutations, Action Inbox backend state machine, Today-to-Action vertical slice,
Chat durable receipt and handoff, Memory Review accept/correct/reject backend
decisions, Evidence Timeline productization, and promotion/proof lanes. These
milestones define goals, routes, model fields, storage semantics, UI outcomes,
proof commands, and authority boundaries; they do not add routes, controls,
runtime calls, connector writes, memory writes, context injection, public beta,
distribution, or production authority by themselves.
UAA-P1-066 remains queued as a strictly read-only Local Model Control Center
inventory/status support lane.

Already-pushed tags remain immutable historical records. M150's
`v1.2.0-alpha` label is preserved as historical alpha-target context only; it
is not the active package baseline.

Current archived release packet refs:

```text
docs/archive/releases/v0_102_3/README_IMPORT.md
docs/archive/releases/v0_102_3/master_plan.md
```

## Operating Model

UAA is built around one rule: agent behavior must be inspectable, permissioned,
reversible, and testable before it can affect real systems.

The current implementation provides:

- typed policy, approval, route, run, receipt, and evidence contracts
- FastAPI route metadata with side-effect classification
- `PolicyEngine` and `LocalApprovalAuthority` as required authority boundaries
- local model readiness through a scoped llama.cpp/OpenWebUI shell lane, with
  OpenWebUI kept secondary to the first-party Control Center product UI
- safe workspace previews, patch proposals, atomic apply, and rollback receipts
- redacted session/run observability for UAA-managed surfaces only
- governed web evidence status and allowlisted evidence request contracts with
  bounded redacted previews and receipt refs
- release verification lanes, Foundation Gate reports, OpenAPI checks, and
  documentation integrity checks
- read-only plugin/skill ecosystem inspection, exact activation records, and
  MCP/A2A compatibility watchlist planning without runtime import or execution

The current baseline explicitly does not grant:

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

Control Center / Founder Command Center is the proprietary first-party product
UI path for Today, Inbox, Plans, Actions, Memory, Evidence, Settings, Models,
and future Chat. OpenWebUI is a supported local/dev shell into UAA-managed local
model behavior, not the agent brain, not the product cockpit, and not the source
of product state. The Python Agent Core remains the authority boundary.

## Capability Map

| Area | Current state | Start here |
|---|---|---|
| Product truth | Evidence-backed release claims and gap matrix | [Product release-truth packet](docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md) |
| Catch-up loop | Human-reconciled loop for ChatGPT/Codex recommendations and peer-gap closure | [operator excellence loop](docs/roadmap/OPERATOR_EXCELLENCE_LOOP.md), [recommendation log](docs/backlog/codex_recommendation_log.md) |
| API contract | **117** OpenAPI paths, stable operation IDs, route metadata | [API boundary](docs/api/README.md), [route inventory](docs/api/route_inventory.md) |
| Governed web evidence | UAA-P1-063 status/request contract, allowlisted HTTPS GET envelope, bounded redacted preview, chatbot disclosure | [governed web evidence](docs/network/GOVERNED_WEB_EVIDENCE_V1.md), [M72 fetch tool](docs/network/READ_ONLY_HTTP_FETCH_TOOL.md) |
| Security posture | Reporting, severity, triage, redaction invariants | [SECURITY.md](SECURITY.md), [triage runbook](docs/security/SECURITY_TRIAGE_RUNBOOK.md) |
| Operator shell | Gap map, route status manifest, and product language rules for visible surfaces | [gap map](docs/control_center/OPERATOR_SHELL_GAP_MAP.md), [route status manifest](docs/control_center/ROUTE_STATUS_MANIFEST.md), [language rules](docs/control_center/PRODUCT_LANGUAGE_RULES.md) |
| Local model lane | llama.cpp/OpenWebUI readiness, smoke harness, evidence matrix | [M167 evidence matrix](docs/production/M167_LIVE_MODEL_EVIDENCE_MATRIX.md), [E2E smoke harness](docs/production/M167_LOCAL_MODEL_E2E_SMOKE_HARNESS.md) |
| Local model operations | Provenance guidance; P0-016 hardens tuning advice; P0-017 adds safe local model operational recovery guidance | [llama-server checklist](docs/production/LLAMA_SERVER_PACKAGING_PROVENANCE_CHECKLIST.md), [operational runbook](docs/production/LOCAL_MODEL_OPERATIONAL_RUNBOOK.md) |
| Workspace workbench | Safe refs, bounded previews, approval-bound mutations, rollback receipts | [file preview policy](docs/files/LOCAL_FILE_REDACTED_PREVIEW_POLICY.md) |
| Durable runs | Append-first local run/receipt storage and lifecycle contracts | [durable run spine](docs/execution/DURABLE_RUN_SPINE.md) |
| Observability | M167 local redacted session/run logging and bounded summary APIs | [session logging](docs/observability/SESSION_LOGGING_M167.md) |
| Performance | p50/p95 release latency baseline and Foundation Gate latency integration | [release latency baseline harness](docs/production/RELEASE_LATENCY_BASELINE_HARNESS.md) |
| Release evidence | Named lanes, evidence packets, backup/restore checks, rollback guidance | [verification lanes](docs/production/RELEASE_VERIFICATION_LANES.md), [evidence packet](docs/production/RELEASE_EVIDENCE_PACKET.md), [backup/restore verification](docs/production/BACKUP_RESTORE_VERIFICATION.md), [rollback runbook](docs/production/LOCAL_STATE_ROLLBACK_RUNBOOK.md) |
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
| Canonical map | [docs/canonical/CANONICAL_DOC_MAP.md](docs/canonical/CANONICAL_DOC_MAP.md) |
| Current roadmap | [docs/canonical/09_roadmap.md](docs/canonical/09_roadmap.md) |
| Operator Runtime Excellence | [roadmap](docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md), [current board](docs/kanban/current_board.md) |
| Operator Excellence catch-up loop | [loop](docs/roadmap/OPERATOR_EXCELLENCE_LOOP.md), [recommendation log](docs/backlog/codex_recommendation_log.md) |
| Current release | [v0.102.3 notes](docs/release_notes/v0_102_3.md), [checkpoint M168](docs/release_notes/checkpoint_m168.md) |

Historical docs live under [docs/archive](docs/archive/README.md). They are
audit artifacts, not current implementation claims.

## Historical Roadmap Anchors

These M34-M60 labels remain active audit anchors. They are historical milestone
markers, not the current package baseline; the current baseline remains
v0.102.3.

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
