# Milestone Charters

Status: Active roadmap governance template maintained through v0.50.0.

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
- M22 is implemented/released by v0.26.0 as contract-only and hardened by v0.26.1; M23 is implemented/released by v0.27.0 as manual fixed-prompt local call only and hardened by v0.27.1; M24 is implemented/released by v0.28.0 as governed local memory provider/store foundation, hardened by v0.28.1, and docs-cleaned by v0.28.2; M25 is implemented/released by v0.29.0 as deterministic local truth/evidence contracts and hardened by v0.29.1 and v0.29.2; M26 is implemented/released by v0.30.0 as deterministic local grounded recall/context-pack contracts and hardened by v0.30.1; M27 is implemented/released by v0.31.0 as validation-only Tool Broker v2 contracts; v0.31.1 is docs-only README polish baseline normalization; M28 is implemented/released by v0.32.0 as Approval Authority v2 + Action Policy Expansion; M29 is implemented/released by v0.33.0 as Agent Task Planning Engine; M30 is implemented/released by v0.34.0 as Multi-Step Execution Framework and hardened by v0.34.1; M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool; M32 is implemented/released by v0.36.0 as Safe Local Filesystem Metadata Tool; M33 is implemented/released by v0.37.0 as First Safe Local File Read Proposal, Redacted Preview Only; M34 is implemented/released by v0.38.0 as Broader File Capability Review planning/docs/verifier only; M35 is implemented/released by v0.39.0 as Safe File Review Workflow Contracts and hardened by v0.39.1 for exact file/path binding; M36 is implemented/released by v0.40.0 as CCC File Review Surface, Review-Only and hardened by v0.40.1 for read-only surface safety; M37 is implemented/released by v0.41.0 as Review Approval Capture, Review-Only Persistence; M38 is implemented/released by v0.42.0 as Safe Context Proposal From Approved Review; M39 is implemented/released by v0.43.0 as CCC Context Proposal Surface; M40 is implemented/released by v0.44.0 as Context Handoff Approval, No Injection; M41 is implemented/released by v0.45.0 as Local Prototype Safety Freeze; M42 is implemented/released by v0.46.0 as Mobile Companion Product Contract Refresh; M43 is implemented/released by v0.47.0 as Mobile API Boundary, Read-Only; M44 is implemented/released by v0.48.0 as CCC iOS Skeleton, No Authority; v0.48.1 hardens the M44 verifier allowance; M45 is implemented/released by v0.49.0 as CCC iOS Local Read-Only Connection; M46 is implemented/released by v0.50.0 as iOS Review/Receipt Read-Only Surfaces; M47-M60 are planned/provisional in `docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md`.
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
by v0.30.1, M27 is implemented/released by v0.31.0, v0.31.1 is docs-only baseline normalization, M28 is implemented/released by v0.32.0 as Approval Authority v2 + Action Policy Expansion, M29 is implemented/released by v0.33.0 as Agent Task Planning Engine, M30 is implemented/released by v0.34.0 as Multi-Step Execution Framework and hardened by v0.34.1, M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool, M32 is implemented/released by v0.36.0 as Safe Local Filesystem Metadata Tool and hardened by v0.36.1, M33 is implemented/released by v0.37.0 as First Safe Local File Read Proposal, Redacted Preview Only, M34 is implemented/released by v0.38.0 as Broader File Capability Review planning/docs/verifier only, M35 is implemented/released by v0.39.0 as Safe File Review Workflow Contracts and hardened by v0.39.1 for exact file/path binding, M36 is implemented/released by v0.40.0 as CCC File Review Surface, Review-Only and hardened by v0.40.1 for read-only surface safety, M37 is implemented/released by v0.41.0 as Review Approval Capture, Review-Only Persistence, M38 is implemented/released by v0.42.0 as Safe Context Proposal From Approved Review, M39 is implemented/released by v0.43.0 as CCC Context Proposal Surface, M40 is implemented/released by v0.44.0 as Context Handoff Approval, No Injection, and M41 is implemented/released by v0.45.0 as Local Prototype Safety Freeze. M42 is implemented/released by v0.46.0 as Mobile Companion Product Contract Refresh. M43 is implemented/released by v0.47.0 as Mobile API Boundary, Read-Only. M44 is implemented/released by v0.48.0 as CCC iOS Skeleton, No Authority. v0.48.1 hardens the M44 verifier allowance. M45 is implemented/released by v0.49.0 as CCC iOS Local Read-Only Connection. M46 is implemented/released by v0.50.0 as iOS Review/Receipt Read-Only Surfaces. M47-M60 remain planned/provisional.

## Review And Hardening Rule

Every new user-facing, API, runtime, mobile, remote, plugin, or design-governance surface should be followed by a focused review or hardening patch before the next major milestone expands scope. Hardening patches must preserve the previous milestone boundary unless a new reviewed milestone explicitly changes it.
