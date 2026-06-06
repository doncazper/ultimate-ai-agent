# Milestone Charters

Status: Active roadmap governance template maintained through v0.84.1.

This document defines the required charter shape for every future milestone prompt. A milestone charter is planning authority only. It does not implement runtime behavior, frontend behavior, backend API routes, provider calls, network calls, remote execution, mobile sensor access, plugin enablement, native build workflows, production persistence, or external actions.

## Required Charter Fields

Every future milestone must state:

- version.
- milestone code.
- title.
- status.
- purpose.
- allowed scope.
- must not add.
- dependencies.
- acceptance criteria.
- review prompt required.
- hardening patch expectation.
- source-of-truth docs.
- notes.

## Standard Template

```text
Version:
Milestone code:
Title:
Status:

Purpose:

Allowed scope:

Must not add:

Dependencies:

Acceptance criteria:

Review prompt required:

Hardening patch expectation:

Source-of-truth docs:

Notes:
```

## Governance Rules

- Python Agent Core remains the brain.
- OpenWebUI is the preferred conversational web shell, not the agent brain.
- CCC means Control Center Clients: CCC Web, CCC iOS, CCC Android, and CCC macOS.
- CCC is the governance/control client family and cannot bypass Approval Authority, Consent Ledger, Tool Broker, Event Ledger, Secret Broker, Foundation Gate, or governed source systems.
- TypeScript Control Center is CCC Web.
- Mobile Companion is a future control, approval, capture, receipt, and status surface, not the agent brain.
- Open Design governs custom CCC surfaces and does not replace OpenWebUI.
- The model is never the source of truth, and model output is not authoritative evidence.
- Consent and credentials are separate.
- Arbitrary string refs are not authority.
- External tools and plugins are not authority.
- Remote worker output is never trusted control input.
- Mobile sensor output is not trusted control input by default.
- Parked work must not become active without an explicit reintroduction prompt.
- No milestone may skip review gates.
- M14-M20 are frozen and implemented through v0.24.0, with v0.24.1 M20 safety hardening accepted, unless a reviewed roadmap patch supersedes them.
- M21 is implemented/released by v0.25.0 as OpenWebUI Bridge + Chat Shell Integration Contract only.
- M22 is implemented/released by v0.26.0 as contract-only and hardened by v0.26.1; M23 is implemented/released by v0.27.0 as manual fixed-prompt local call only and hardened by v0.27.1; M24 is implemented/released by v0.28.0 as governed local memory provider/store foundation, hardened by v0.28.1, and docs-cleaned by v0.28.2; M25 is implemented/released by v0.29.0 as deterministic local truth/evidence contracts and hardened by v0.29.1 and v0.29.2; M26 is implemented/released by v0.30.0 as deterministic local grounded recall/context-pack contracts and hardened by v0.30.1; M27 is implemented/released by v0.31.0 as validation-only Tool Broker v2 contracts; v0.31.1 is docs-only README polish baseline normalization; M28 is implemented/released by v0.32.0 as Approval Authority v2 + Action Policy Expansion; M29 is implemented/released by v0.33.0 as Agent Task Planning Engine; M30 is implemented/released by v0.34.0 as Multi-Step Execution Framework and hardened by v0.34.1; M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool; M32 is implemented/released by v0.36.0 as Safe Local Filesystem Metadata Tool; M33 is implemented/released by v0.37.0 as First Safe Local File Read Proposal, Redacted Preview Only; M34 is implemented/released by v0.38.0 as Broader File Capability Review planning/docs/verifier only; M35 is implemented/released by v0.39.0 as Safe File Review Workflow Contracts and hardened by v0.39.1 for exact file/path binding; M36 is implemented/released by v0.40.0 as CCC File Review Surface, Review-Only and hardened by v0.40.1 for read-only surface safety; M37 is implemented/released by v0.41.0 as Review Approval Capture, Review-Only Persistence; M38 is implemented/released by v0.42.0 as Safe Context Proposal From Approved Review; M39 is implemented/released by v0.43.0 as CCC Context Proposal Surface; M40 is implemented/released by v0.44.0 as Context Handoff Approval, No Injection; M41 is implemented/released by v0.45.0 as Local Prototype Safety Freeze; M42 is implemented/released by v0.46.0 as Mobile Companion Product Contract Refresh; M43 is implemented/released by v0.47.0 as Mobile API Boundary, Read-Only; M44 is implemented/released by v0.48.0 as CCC iOS Skeleton, No Authority; v0.48.1 hardens the M44 verifier allowance; M45 is implemented/released by v0.49.0 as CCC iOS Local Read-Only Connection; M46 is implemented/released by v0.50.0 as iOS Review/Receipt Read-Only Surfaces; M47 is implemented/released by v0.51.0 as TestFlight Pipeline, Internal Only; M48 is implemented/released by v0.52.0 as First Internal TestFlight Build; M49 is implemented/released by v0.53.0 as Mobile Review Approval Capture; M50 is implemented/released by v0.54.0 as Mobile Approval Audit Hardening; M51 is implemented/released by v0.55.0 as OpenWebUI Bridge Adapter Pilot; M52 is implemented/released by v0.56.0 as OpenWebUI Safe Conversation Surface; M53 is implemented/released; M54 is implemented/released; M55 is implemented/released; M56 is implemented/released; M57 is implemented/released; M58 is implemented/released; M59 is implemented/released and M60 is implemented/released in `docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md`.
- M61 is implemented/released by v0.65.0 as Autonomy Mode Charter + Authority Levels, M62 is implemented/released by v0.66.0 as Scoped Autonomy Session Contracts, M63 is implemented/released by v0.67.0 as Autonomy Policy Engine v1, M64 is implemented/released by v0.68.0 as Autonomous Plan Simulator, M65 is implemented/released by v0.69.0 as Autonomy Audit + Replay Viewer, M66 is implemented/released by v0.70.0 as Scoped Approval Bundles, M67 is implemented/released by v0.71.0 as Revocation + Kill Switch, M68 is implemented/released by v0.72.0 as Autonomy Risk Classifier, M69 is implemented/released by v0.73.0 as Low-Risk Autonomous Dry Run, M70 is implemented/released by v0.74.0 as Autonomy Foundation Freeze, M71 is implemented/released by v0.75.0 as Network Tool Contract Review, M72 is implemented/released by v0.76.0 as Read-Only HTTP Fetch Tool, Allowlisted, M73 is implemented/released by v0.77.0 as Browser Automation Contract Review, M74 is implemented/released by v0.78.0 as Browser Observe-Only Adapter, M75 is implemented/released by v0.79.0 as Browser Action Dry-Run Planner, M76 is implemented/released by v0.80.0 as OpenWebUI Runtime Bridge v1, M77 is implemented/released by v0.81.0 as OpenWebUI Safe Handoff Execution, M78 is implemented/released by v0.82.0 as Plugin Manifest Security Model, M79 is implemented/released by v0.83.0 as Plugin Install Review, Disabled by Default, and M80 is implemented/released by v0.84.0 as Network/Browser/OpenWebUI Hardening Freeze and currentness-repaired by v0.84.1. M81-M100 remain planned/provisional in `docs/roadmap/M61_M100_ROADMAP.md`.
- Future prompts after M20 must read `docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md`, `docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md`, and `docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md`.

## M19 Current Status

v0.23.0 / M19 is implemented as Mobile Companion Contract/API Planning only.
M19 adds contract models, validation helpers, docs, tests, verifier coverage,
and Foundation Gate criteria. It adds no mobile app, no Android app, no iOS
app, no native build workflow, no OS permission integration, no mobile sensor
access, no backend API route, and no OpenAPI path count change. Device
Capability Broker is required before sensors. Capture cannot silently become
memory. Phone/mobile is not the agent brain. M20 is implemented/released as
Device Capability Broker Contract only.

v0.23.1 hardens M19 roadmap status and mobile contract safety tests only. It
adds no M20 Device Capability Broker implementation, mobile app, Android app,
iOS app, macOS app, native build workflow, mobile sensor access, OS permission
integration, backend API route, dependency, runtime execution, model/provider
call, remote execution, plugin enablement, or production authority.

v0.24.0 implements M20 Device Capability Broker Contract as contract-only
planning and validation. It adds no Device Capability Broker runtime
implementation, mobile app, Android app, iOS app, macOS app, native build
workflow, mobile sensor access, OS permission integration, background service,
notification runtime, backend API route, dependency, runtime execution,
model/provider call, remote execution, plugin enablement, OpenWebUI
integration, or production authority. M21-M40 remain planned/provisional.

v0.24.1 hardens M20 Device Capability Broker Contract safety only. It adds no
M21 implementation, Device Capability Broker runtime implementation, mobile
app, Android app, iOS app, macOS app, native build workflow, sensor API, OS
permission code, backend API route, dependency, runtime execution,
model/provider call, remote execution, plugin enablement, architecture behavior
change, or production authority.

v0.25.0 implements M21 OpenWebUI Bridge + Chat Shell Integration Contract as
contract/planning/validation only. It adds no OpenWebUI integration,
deployment config, Docker config, OpenWebUI plugin/function/pipeline/tool/admin
workflow, backend API route, frontend feature, runtime execution, local LLM
call, model/provider call, tool execution, memory write, file access, remote
execution, browser automation, Computer Use, mobile sensor access, plugin
enablement, dependency, or production authority. M22 is implemented/released
contract-only by v0.26.0, hardened by v0.26.1, and M23 is implemented/released
by v0.27.0 as manual fixed-prompt local call only and hardened by v0.27.1.
M24 is implemented/released by v0.28.0 as governed local memory provider/store
foundation. M25 is implemented/released by v0.29.0 as deterministic local
truth/evidence contracts. M26 is implemented/released by v0.30.0 and hardened
by v0.30.1, M27 is implemented/released by v0.31.0, v0.31.1 is docs-only baseline normalization, M28 is implemented/released by v0.32.0 as Approval Authority v2 + Action Policy Expansion, M29 is implemented/released by v0.33.0 as Agent Task Planning Engine, M30 is implemented/released by v0.34.0 as Multi-Step Execution Framework and hardened by v0.34.1, M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool, M32 is implemented/released by v0.36.0 as Safe Local Filesystem Metadata Tool and hardened by v0.36.1, M33 is implemented/released by v0.37.0 as First Safe Local File Read Proposal, Redacted Preview Only, M34 is implemented/released by v0.38.0 as Broader File Capability Review planning/docs/verifier only, M35 is implemented/released by v0.39.0 as Safe File Review Workflow Contracts and hardened by v0.39.1 for exact file/path binding, M36 is implemented/released by v0.40.0 as CCC File Review Surface, Review-Only and hardened by v0.40.1 for read-only surface safety, M37 is implemented/released by v0.41.0 as Review Approval Capture, Review-Only Persistence, M38 is implemented/released by v0.42.0 as Safe Context Proposal From Approved Review, M39 is implemented/released by v0.43.0 as CCC Context Proposal Surface, M40 is implemented/released by v0.44.0 as Context Handoff Approval, No Injection, and M41 is implemented/released by v0.45.0 as Local Prototype Safety Freeze. M42 is implemented/released by v0.46.0 as Mobile Companion Product Contract Refresh. M43 is implemented/released by v0.47.0 as Mobile API Boundary, Read-Only. M44 is implemented/released by v0.48.0 as CCC iOS Skeleton, No Authority. v0.48.1 hardens the M44 verifier allowance. M45 is implemented/released by v0.49.0 as CCC iOS Local Read-Only Connection. M46 is implemented/released by v0.50.0 as iOS Review/Receipt Read-Only Surfaces. M47 is implemented/released by v0.51.0 as TestFlight Pipeline, Internal Only. M48 is implemented/released by v0.52.0 as First Internal TestFlight Build. M49 is implemented/released by v0.53.0 as Mobile Review Approval Capture. M50 is implemented/released by v0.54.0 as Mobile Approval Audit Hardening. M51 is implemented/released by v0.55.0 as OpenWebUI Bridge Adapter Pilot. M52 is implemented/released by v0.56.0 as OpenWebUI Safe Conversation Surface. M53 is implemented/released. M54 is implemented/released. M55 is implemented/released. M56 is implemented/released. M57 is implemented/released. M58 is implemented/released. M59 is implemented/released as Public GitHub Readiness and M60 is implemented/released as Local Developer Beta Freeze.

## Review And Hardening Rule

Every new user-facing, API, runtime, mobile, remote, plugin, or design-governance surface should be followed by a focused review or hardening patch before the next major milestone expands scope. Hardening patches must preserve the previous milestone boundary unless a new reviewed milestone explicitly changes it.
