# 09 - Roadmap v0.25.0

Status: Active foundation-first roadmap. This is the single roadmap source of truth.

## North Star

Build a Commander-led, spec-driven, memory-backed, relationship-aware AI operating system that turns vague goals into verified completed outcomes while remaining inspectable, permissioned, reversible, modular, scalable, and user-controlled.

## Stack baseline

```text
Python/FastAPI/Pydantic Agent Core
CCC Web / TypeScript Control Center
OpenWebUI preferred conversational web shell
Postgres canonical database
Docker Compose local development
Stable Agent API Boundary
```

OpenWebUI is a window into the agent, not the agent brain. CCC means Control Center Clients: CCC Web, CCC iOS, CCC Android, and CCC macOS.

## Foundation Phase Context

The original foundation sequence established runtime hygiene, local runtime/context survival, truth/grounding/evidence governance, observability standards mapping, and Minimum Lovable Kernel preparation. Current accepted work is tracked in the release baseline below.

## Current accepted baseline

The active accepted baseline is v0.25.0. It implements v0.25.0 / M21 OpenWebUI Bridge + Chat Shell Integration Contract as contract/planning/validation only. v0.24.0 / M20 remains implemented/released as Device Capability Broker Contract only, and v0.24.1 remains its safety hardening patch. v0.23.0 / M19 is implemented/released as contract/API planning only. M22-M40 remain planned/provisional.

v0.25.0 adds:

- OpenWebUI bridge contract models, validation helpers, manifest builders, plan builders, and receipt planning.
- OpenWebUI bridge docs covering the chat shell contract, session/transcript refs, security model, authority boundary, non-goals, and future integration stages.
- tests and Foundation Gate coverage for M21 contract-only safety.
- static verifier coverage for forbidden OpenWebUI runtime/config/dependency/route drift.

v0.25.0 does not add OpenWebUI integration, deployment config, Docker config, OpenWebUI plugin/function/pipeline/tool/admin/auth/cookie/API key/admin token workflow, browser profile access, live OpenWebUI connection, backend API route, frontend feature, runtime execution, local LLM call, model/provider call, tool execution, memory write, file access, remote execution, browser automation, Computer Use, mobile sensor access, plugin enablement, dependency, or production authority.

v0.24.1 adds:

- validator hardening for enabled and implemented capability flags, permission runtime claims, notification push runtime claims, background service runtime claims, validation decision allow claims, redacted receipt requirements, contract-only revocation plans, raw payload-like metadata, geolocation coordinates, private local paths, and secret-like metadata.
- expanded tests for every major device capability rejecting current enablement and implementation claims.
- static verifier and Foundation Gate hardening for expanded device/mobile route drift and sensor/native API fragments.
- docs hardening that says no device capability is enabled or implemented, user gesture is future contract metadata only, raw payloads are blocked, receipts remain redacted, and M21 remains planned/provisional.
- no M21 OpenWebUI Bridge, Device Capability Broker runtime implementation, mobile app, native build workflow, sensor API, OS permission code, backend API route, dependency, runtime execution, model/provider call, remote execution, plugin enablement, architecture behavior change, or production authority.

v0.24.0 adds:

- `src/ultimate_ai_agent/core/device_capabilities/` contract-only models, enums, manifest builders, validation helpers, policy helpers, and receipt plan helpers.
- `docs/device_capabilities/` contract docs for manifest schema, permission lifecycle, capture intent, sensor boundary, trust/revocation, receipts/redaction, security model, and non-goals.
- documentation-integrity verifier coverage for M20 docs and M21 planned/provisional status.
- Foundation Gate coverage for M20 contract-only/no-sensor/no-authority boundaries.
- no backend route, frontend feature, runtime execution, manual smoke execution, model/provider call, remote execution, mobile sensor access, plugin enablement, OpenWebUI integration, dependency, architecture behavior change, native build workflow, mobile app, Android app, iOS app, macOS app, OS permission integration, background service, notification runtime, device pairing runtime, or production Control Center authority.

v0.23.1 hardens M19 Mobile Companion Contract/API Planning and cleans up roadmap currentness after v0.23.0. It updates active roadmap docs so v0.23.0 / M19 is implemented/released and M20/post-M20 milestones remain planned/provisional, strengthens documentation integrity checks for stale roadmap status labels, and deepens mobile contract tests for contacts/calendar capability denial, secret-like metadata refs, external-send blocking, OS-permission integration blocking, and background-service blocking.

v0.23.0 implements M19 Mobile Companion Contract/API Planning only. It adds Python contract models, validation helpers, docs, tests, static verifier coverage, and Foundation Gate criteria for future CCC iOS/Android/mobile companion planning. OpenAPI path count remains `74`. It adds no M20 Device Capability Broker implementation, backend API route, frontend feature, Android app, iOS app, macOS app, native build workflow, OS permission integration, mobile sensor access, mobile approval execution, runtime execution, manual smoke execution, model/provider call, remote execution, plugin enablement, OpenWebUI integration, dependency, architecture behavior change, or production Control Center authority.

v0.22.0 implements M18 Local Runtime Status + Manual Smoke Control Surface in CCC Web only. It adds read-only `/runtime/local`, validation-only `/runtime/manual-smoke`, safe mock summaries, tests, docs, verifier coverage, and Foundation Gate criteria. It adds no backend API route, OpenAPI path count change, runtime execution, manual smoke execution, model/provider call, local runtime provider integration, remote execution, mobile sensor access, plugin enablement, OpenWebUI integration, dependency, native build workflow, or production Control Center authority.

v0.18.4 adds:

- `docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md`.
- `docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md`.
- `docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md`.
- `docs/roadmap/ECOSYSTEM_WATCHLIST.md`.
- `docs/roadmap/STANDARDS_ALIGNMENT_WATCHLIST.md`.
- M21-M40 planned/provisional capability-layer charters after the frozen M14-M20 sequence.
- conservative documentation verifier and Foundation Gate checks for post-M20 roadmap projection.
- no implementation of M21-M40 capabilities, backend route, frontend behavior, runtime execution, model/provider call, network call, remote execution, mobile sensor access, plugin enablement, dependency, native build workflow, or external action.

v0.18.3 adds:

- `docs/ui/*` OpenWebUI and CCC strategy docs.
- OpenWebUI as the preferred conversational web shell, not the agent brain.
- CCC as Control Center Clients: CCC Web, CCC iOS, CCC Android, and CCC macOS.
- CCC Web as the current TypeScript web Control Center.
- CCC iOS, CCC Android, and CCC macOS as future native clients only.
- Open Design as governance for custom CCC surfaces, not a replacement for OpenWebUI.
- conservative documentation verifier and Foundation Gate checks for OpenWebUI/CCC strategy.
- no OpenWebUI integration, deployment config, frontend feature, backend route, native app, native build workflow, mobile sensor access, OS permission integration, signing/store workflow, dependency, or production authority.

v0.18.2 added:

- `docs/design/*` as repo-owned design governance.
- Control Center design language, status/risk visual language, accessibility baseline, UI copy/action language, component taxonomy, responsive layout baseline, design artifact governance, design tooling policy, and design token roadmap.
- conservative documentation verifier and Foundation Gate checks for design governance.
- no UI behavior, backend route, dependency, design tool enablement, or production authority.

v0.17.5 resolved the M14 ambiguity:

- M14 is Web Control Center Local Backend Connection Stabilization.
- Approval Queue + Receipt/Event Viewer UI moves to M15.
- local browser smoke / UX polish was v0.17.4, not M14.

v0.19.0 implements M15 Approval Queue + Receipt/Event Viewer UI as frontend-only CCC Web inspection panels. It does not add backend API paths, OpenWebUI integration, OpenWebUI deployment config, runtime execution, local model execution, model/provider calls, network calls, remote dispatch, native CCC implementation, Android app, iOS app, macOS app, mobile app or sensor code, Device Capability Broker implementation, MCP runtime support, Agent Skills runtime support, AGENTS.md runtime loading, sandbox execution, tool execution, browser automation, Computer Use, OS permission integration, signing, keystore, provisioning, App Store or Play Store workflow, plugin enablement, dependencies, auth, credentials, cookies, analytics/SaaS SDKs, design tool integration, external API hosts, or production Control Center authority.

v0.19.1 hardens M15 Approval/Receipt UI safety as frontend/static-verifier/Foundation Gate work only. It requires authority-boundary copy, approval-ref identifier-only copy, Python Agent Core approval authority copy, redacted receipt/event detail copy, raw M15 review field rejection, and credential-like review field rejection. It does not start M16, add backend API paths, approval execution, approve/deny mutation, runtime execution, model/provider calls, network calls, remote execution, mobile sensor access, plugin enablement, dependencies, native build workflow, or production Control Center authority.

v0.20.0 implements M16 Event Timeline + Run/Receipt Trace Viewer as frontend-only CCC Web work. It adds `/events/timeline`, redacted timeline summaries, selected run/receipt trace summaries, relation refs, safe Foundation Gate evidence summaries, frontend tests, static verifier checks, docs, and Foundation Gate coverage. It adds no backend API paths, OpenAPI path count change, approval execution, tool execution, runtime execution, model/provider calls, network calls, remote execution, mobile sensor access, plugin enablement, dependencies, native build workflow, external telemetry export, raw payload display, or production Control Center authority.

v0.20.1 hardens M16 trace/redaction safety as frontend/test/verifier/Foundation Gate/docs work only. It adds second-trace selection coverage, accessible selected-card state, OpenAPI path-count/no-backend-route M16 gate checks, generated build/log artifact verifier coverage, and review-build hygiene docs. It adds no backend API paths, OpenAPI path count change, M17 Evidence/File/Memory Viewer, execution, export, model/provider calls, remote execution, mobile sensor access, plugin enablement, dependencies, native build workflow, raw payload display, or production Control Center authority.

v0.21.0 implements M17 Evidence/File/Memory Viewer as frontend-only CCC Web work. It adds `/evidence`, `/files`, and `/memory` routes with redacted evidence refs, safe file refs, recall-only memory refs, frontend tests, static verifier checks, docs, and Foundation Gate coverage. It adds no backend API paths, OpenAPI path count change, file mutation, memory mutation, filesystem browsing, runtime execution, model/provider calls, remote execution, mobile sensor access, plugin enablement, dependencies, native build workflow, raw payload display, embeddings, vector DB, memory provider implementation, or production Control Center authority.

v0.21.1 hardens M17 Evidence/File/Memory Viewer as frontend/test/verifier/Foundation Gate/docs work only. It adds alternate safe mock refs, accessible selected-card reviewability, frontend tests, static verifier checks, browser smoke reviewability, and Foundation Gate criteria. It adds no M18 Local Runtime Status + Manual Smoke Control Surface, backend API paths, OpenAPI path count change, file mutation, memory mutation, filesystem browsing, runtime execution, model/provider calls, remote execution, mobile sensor access, plugin enablement, dependencies, auth, cookies, analytics, SaaS SDKs, native build workflow, raw payload display, embeddings, vector DB, memory provider implementation, or production Control Center authority.

v0.21.2 normalizes developer environment commands as dev tooling/docs work only. It adds repo-local Makefile targets and `scripts/verify_dev_environment.py` so Codex and local shells use `.venv/bin/python` rather than relying on a bare `python` binary on PATH. It adds no M18 Local Runtime Status + Manual Smoke Control Surface, runtime feature, frontend feature, backend API path, OpenAPI path count change, dependency, global tool install, application behavior change, runtime/model/provider call, network call, mobile/native/browser/computer-use functionality, plugin enablement, or production capability.

## Accepted baseline through v0.25.0

The active accepted baseline includes foundation modules through M10.5 plus documentation integrity synchronization, Codex plugin/external tooling governance, M11 runtime readiness/report validation, M12 Control Center backend contract/API foundation, M13 Web Control Center read-only frontend shell with CI/static/browser-readiness hardening, the v0.17.5 roadmap charter freeze, M14 local backend connection stabilization and safety hardening, v0.18.2 design governance, v0.18.3 OpenWebUI/CCC client strategy clarification, v0.18.4 post-M20 roadmap projection, v0.19.0 M15 Approval Queue + Receipt/Event Viewer UI, v0.19.1 M15 Approval/Receipt UI safety hardening, v0.20.0 M16 Event Timeline + Run/Receipt Trace Viewer, v0.20.1 M16 trace/redaction safety hardening, v0.21.0 M17 Evidence/File/Memory Viewer, v0.21.1 M17 safety hardening, v0.21.2 developer environment command normalization, v0.22.0 M18 Local Runtime Status + Manual Smoke Control Surface, v0.22.1 roadmap status label cleanup, v0.23.0 M19 Mobile Companion Contract/API Planning, v0.23.1 M19 roadmap/mobile-contract safety cleanup, v0.24.0 M20 Device Capability Broker Contract, v0.24.1 M20 safety hardening, and v0.25.0 M21 OpenWebUI Bridge + Chat Shell Integration Contract. v0.17.4 polished local shell reviewability and browser smoke reporting only; it did not start M14, add backend API paths, add dependencies, add production Control Center authority, or add execution capability.

Recent accepted milestones:

```text
v0.14.0 — M10 manual local loopback smoke harness, manual-only and fixed-prompt-only
v0.14.1 — M10.5 remote worker foundation and planned tailnet transport metadata
v0.14.2 — M10.5 policy hardening for loopback/runtime and approval validation
v0.14.3 — open-source-first private mesh taxonomy with planned Headscale/generic WireGuard/Tailscale metadata
v0.14.4 — Mobile Companion and Device Capability Broker roadmap planning only
v0.14.5 — documentation integrity, canonical map, docs index, and documentation verifier
v0.14.6 — Codex plugin and external build tool governance inventory, docs/policy only
v0.15.0 — M11 runtime readiness gate, capability matrix, and manual smoke report validation
v0.15.1 — M11 runtime readiness taxonomy clarification for local loopback policy and fake smoke origins
v0.16.0 — M12 Control Center contract and read-only dashboard API foundation
v0.17.0 — M13 Web Control Center read-only frontend shell
v0.17.1 — M13 Web Control Center frontend safety polish
v0.17.2 — M13 Web Control Center CI, static safety, and local browser smoke readiness hardening
v0.17.3 — documentation current-release label cleanup
v0.17.4 — Web Control Center local browser smoke polish and safe reporting docs
v0.17.5 — Roadmap Projection + M14-M20 Milestone Charter Freeze
v0.18.0 — M14 Web Control Center Local Backend Connection Stabilization
v0.18.1 — M14 Hardening: Control Center Backend Connection Safety
v0.18.2 — Open Design System + UI Design Governance
v0.18.3 — OpenWebUI + CCC Client Strategy Clarification
v0.18.4 — Post-M20 Roadmap Projection + M21-M40 Capability Layer Charters
v0.19.0 — M15 Approval Queue + Receipt/Event Viewer UI
v0.19.1 — M15 Approval/Receipt UI Safety Hardening
v0.20.0 — M16 Event Timeline + Run/Receipt Trace Viewer
v0.20.1 — M16 Trace/Redaction Safety Hardening
v0.21.0 — M17 Evidence/File/Memory Viewer
v0.21.1 — M17 Evidence/File/Memory Viewer Safety Hardening
v0.21.2 — Developer Environment Command Normalization
v0.22.0 — M18 Local Runtime Status + Manual Smoke Control Surface
v0.22.1 — Roadmap Status Label Cleanup After M18
v0.23.0 — M19 Mobile Companion Contract/API Planning
v0.23.1 — M19 Roadmap Status + Mobile Contract Safety Hardening
v0.24.0 — M20 Device Capability Broker Contract
v0.24.1 — M20 Device Capability Broker Contract Safety Hardening
v0.25.0 — M21 OpenWebUI Bridge + Chat Shell Integration Contract

- adds local React/Vite/TypeScript app under `apps/control-center`.
- consumes existing read-only/preview-only backend routes.
- provides safe mock fallback data for local development.
- action preview UI posts only to `/control-center/actions/preview`.
- v0.17.1 and v0.17.2 harden frontend safety verification, CI coverage, and manual local browser smoke readiness.
- v0.17.3 keeps current-release documentation labels aligned with the active baseline.
- v0.17.4 improves route headings, accessible UI states, action preview risk metadata display, mock fallback reviewability, and local browser smoke reporting docs.
- v0.17.5 freezes the M14-M20 roadmap sequence and does not add implementation capability.
- v0.18.0 adds local-only backend connection policy and visible live/degraded/mock fallback states for M14.
- v0.18.1 hardens M14 local backend connection safety.
- v0.18.2 adds repo-owned Open Design System and UI Design Governance docs before M15.
- v0.18.3 clarifies OpenWebUI and CCC Web/iOS/Android/macOS strategy before M15.
- v0.18.4 adds post-M20 roadmap projection and M21-M40 planned/provisional capability-layer charters.
- v0.19.0 adds read-only/preview-only approval queue, receipt viewer, and event viewer frontend routes.
- v0.19.1 hardens M15 approval authority and redacted-detail safety checks.
- v0.20.0 adds read-only event timeline and run/receipt trace viewer summaries.
- v0.20.1 hardens M16 trace selection coverage, OpenAPI/no-backend-route checks, and generated artifact hygiene.
- v0.21.0 adds read-only evidence, file ref, and memory ref summary viewers.
- v0.21.1 hardens M17 selected-state reviewability, alternate safe mock refs, tests, verifiers, docs, and Foundation Gate checks.
- v0.21.2 adds repo-local developer verification command normalization using `.venv/bin/python` and Makefile targets.
- v0.22.0 adds read-only local runtime status and validation-only manual smoke report summary surfaces.
- v0.22.1 cleans up roadmap status labels after M18 without adding capability.
- v0.23.0 implements M19 Mobile Companion Contract/API Planning only.
- v0.23.1 hardens M19 roadmap currentness and mobile contract safety tests without adding capability.
- v0.24.0 implements M20 Device Capability Broker Contract as contract-only planning and validation.
- keeps backend OpenAPI path count unchanged at `74`.
- adds no runtime execution, model/provider calls, OpenWebUI integration, remote dispatch, mobile sensors, OS permission integration, backend device routes, plugin enablement, native builds, Chrome/Computer Use automation, design tool enablement, native CCC implementation, M21-M40 implementation, or production authority.
```

## Next canonical sequence from v0.17.5

The detailed sequence is frozen in `docs/roadmap/NEXT_SEQUENCE_v0_17_5.md`. The milestone charter template is `docs/roadmap/MILESTONE_CHARTERS.md`. These files must be checked before writing future milestone prompts.

v0.18.0 and v0.18.1 have implemented and hardened M14 from that sequence. v0.18.2 has implemented the Open Design governance milestone. v0.18.3 has implemented OpenWebUI and CCC Client Strategy clarification. v0.18.4 has implemented post-M20 roadmap projection docs. v0.19.0 has implemented M15 frontend-only Approval Queue + Receipt/Event Viewer UI. v0.19.1 has hardened M15 Approval/Receipt UI safety. v0.20.0 has implemented M16 frontend-only Event Timeline + Run/Receipt Trace Viewer. v0.20.1 has hardened M16 trace/redaction safety. v0.21.0 has implemented M17 frontend-only Evidence/File/Memory Viewer. v0.21.1 has hardened M17 evidence/file/memory viewer safety. v0.21.2 has normalized developer environment commands. v0.22.0 has implemented M18 frontend-only Local Runtime Status + Manual Smoke Control Surface. v0.22.1 has cleaned up roadmap status labels only. v0.23.0 has implemented/released M19 Mobile Companion Contract/API Planning only. v0.23.1 has hardened M19 roadmap currentness and mobile contract safety tests only. v0.24.0 has implemented/released M20 Device Capability Broker Contract only. v0.24.1 has hardened M20 Device Capability Broker Contract safety only. v0.25.0 has implemented/released M21 OpenWebUI Bridge + Chat Shell Integration Contract as contract/planning/validation only. M22 and M23 remain planned/provisional until superseded by reviewed roadmap patches.

```text
v0.17.5 — Roadmap Projection + M14-M20 Milestone Charter Freeze, docs-only
v0.18.0 / M14 — Web Control Center Local Backend Connection Stabilization, implemented
v0.18.1 — M14 Hardening: Control Center Backend Connection Safety, implemented
v0.18.2 — Open Design System + UI Design Governance, implemented
v0.18.3 — OpenWebUI + CCC Client Strategy Clarification, implemented
v0.18.4 — Post-M20 Roadmap Projection + M21-M40 Capability Layer Charters, docs-only
v0.19.0 / M15 — Approval Queue + Receipt/Event Viewer UI, implemented read-only/preview-only
v0.19.1 — M15 Hardening: Approval/Receipt UI Safety, implemented
v0.20.0 / M16 — Event Timeline + Run/Receipt Trace Viewer, implemented read-only
v0.20.1 — M16 Hardening: Trace/Redaction Safety + Whole-Code Bug Audit, implemented
v0.21.0 / M17 — Evidence/File/Memory Viewer, implemented read-only
v0.21.1 — M17 Hardening: Evidence/File/Memory Viewer Safety, implemented
v0.21.2 — Developer Environment Command Normalization, implemented
v0.22.0 / M18 — Local Runtime Status + Manual Smoke Control Surface, implemented read-only/validation-only
v0.22.1 — Roadmap Status Label Cleanup After M18, docs-only
v0.23.0 / M19 — Mobile Companion Contract/API Planning, implemented/released contract/API planning only
v0.23.1 — M19 Roadmap Status + Mobile Contract Safety Hardening, implemented cleanup/hardening only
v0.24.0 / M20 — Device Capability Broker Contract, implemented/released contract-only
v0.25.0 / M21 — OpenWebUI Bridge + Chat Shell Integration Contract, implemented/released contract-only
v0.26.0 / M22 — Local Model Runtime Activation Contract, planned/provisional
v0.27.0 / M23 — First Real Local LLM Call, Non-Tool, Non-Authoritative, planned/provisional
v0.28.0 / M24 — Memory Provider Abstraction + Local Memory Store, planned/provisional
v0.29.0 / M25 — Truth Source Router + Evidence Claim Checker, planned/provisional
v0.30.0 / M26 — Tool Execution Sandbox Contract, Dry-Run Only, planned/provisional
v0.31.0 / M27 — MCP / Agent Skills / AGENTS.md Trust Registry, Quarantine-Only, planned/provisional
v0.32.0 / M28 — Local Sandbox Backend Abstraction, planned/provisional
v0.33.0 / M29 — First Low-Risk Tool Dry-Run + Approval Preview, planned/provisional
v0.34.0 / M30 — First Approved Low-Risk Local Tool Execution, planned/provisional
v0.35.0 / M31 — CCC Native Client Contract: iOS / Android / macOS, planned/provisional
v0.36.0 / M32 — Device Pairing + Trust Handshake Contract, planned/provisional
v0.37.0 / M33 — Mobile Approval Surface Prototype, No Sensors, planned/provisional
v0.38.0 / M34 — macOS Local Companion Contract / Prototype, planned/provisional
v0.39.0 / M35 — Device Capability Broker Implementation, No Sensors Yet, planned/provisional
v0.40.0 / M36 — Mobile Capture Inbox, Selected Input Only, planned/provisional
v0.41.0 / M37 — One Governed Sensor Capability, planned/provisional
v0.42.0 / M38 — Browser Automation Contract, No Execution, planned/provisional
v0.43.0 / M39 — Observability Export Adapters, planned/provisional
v0.44.0 / M40 — Agent Evaluation + Regression Harness, planned/provisional
```

M14 is not local browser smoke / UX polish. That work was v0.17.4. M15 is the first planned approval queue plus receipt/event viewer UI milestone, and it remains read-only/preview-only unless a future backend contract explicitly changes that boundary.

Post-M20 source-of-truth docs:

- `docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md`.
- `docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md`.
- `docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md`.
- `docs/roadmap/ECOSYSTEM_WATCHLIST.md`.
- `docs/roadmap/STANDARDS_ALIGNMENT_WATCHLIST.md`.

## Minimum Lovable Kernel

Before committing to the full foundation build, prove one genuine end-to-end task:

```text
Create a local project artifact through the agent kernel.
Use Execution Contract + Context Pack.
Use Result/Error Envelope.
Use ActorContext and TemporalContext.
Use Data Classification and Redaction policy.
Use idempotency metadata for the file mutation.
Check Consent Ledger.
Route File Manager through Tool Broker.
Write an actual file.
Log event-level cost attribution.
Create rollback metadata.
Verify the artifact and receipt.
Write source-linked memory.
```

## Historical Foundation Gate Sequence

```text
M0 — Repository, Canonical Foundation, and Stack Skeleton
M0.5 — Runtime Hygiene Primitives: Result/Error, Idempotency, Actor, Time, Classification, Redaction, Boundaries
M1 — Kernel Contracts: Execution Contract + Context Pack, v0/provisional
M2 — Event Ledger, Deterministic Run State, Receipts, and Observability Standards Mapping
M2.5 — World State, Context Budget, Local Runtime, and SDK Adapter Boundaries
M3 — Consent Ledger + Tool Broker
M3.5 — Secret Broker + Provider Registry + Normalized Provider Envelopes
M4 — Memory Service + File Manager
M4.5 — Truth Source Router and Evidence Governance
M5 — Minimum Lovable Kernel Vertical Slice
M6 — Contract Tests, Shadow Replay, Foundation Gate Decision
```

## M0 acceptance

```text
Repo layout exists.
Python Agent Core skeleton exists.
JSON/schema validation command exists.
Prompt registry validation command exists.
FastAPI health/API boundary placeholder exists.
Docker Compose Postgres scaffold exists.
OpenWebUI config is present only as optional shell.
Foundation-first rule is visible.
No advanced modules are implemented.
```

## M0.5 acceptance

```text
ResultEnvelope and ErrorEnvelope schemas validate.
Idempotency/retry policy schema validates.
ActorContext schema validates.
TemporalContext schema validates.
Data classification schema validates.
Redaction policy schema validates.
Capability flag schema validates.
Service boundary rules are documented.
Test strategy v0 is documented.
```

## M1 acceptance

```text
Execution Contract and Context Pack schemas/models validate.
Contracts are marked v0/provisional.
Advanced modules are rejected until Foundation Gate.
Verification contract references are supported.
Runtime hygiene primitives are referenced by contracts.
```

## M2 acceptance

```text
Run/event records support append-only logging.
Event-level cost attribution exists.
Events include trace/correlation/actor/temporal/classification metadata.
Receipts can be generated without secrets.
Custom deterministic state machine is documented as initial durable-execution substrate.
Event Ledger records are mappable to OpenTelemetry GenAI spans/events/metrics without changing internal ledger semantics.
W3C Trace Context is documented as the trace propagation standard, and trace-compatible IDs can propagate across API, worker, model-router, Tool Broker, provider, MCP, SDK, and A2A boundaries.
CloudEvents export and AsyncAPI documentation are planned as future compatibility layers for event streams, not M2 implementation blockers.
Redaction policy applies before any telemetry export.
```

## M2.5 acceptance

```text
Structured World State schemas validate.
Context Budget Manager schemas validate.
Context-limit discovery policy is documented.
Token accounting and calibration schemas validate.
Tool-result retention/trimming policy is documented.
Prompt/tool bundle cache policy is documented.
Local runtime manifests and health profiles validate.
Privacy routing policy validates.
Agent SDK and A2A adapters are documented as boundary adapters only.
Long-running session survival eval is specified.
```

## M3 acceptance

```text
Consent grants can be created, checked, expired, revoked, and audited.
Tool calls are schema-validated, consent-checked, risk-classified, logged, and rollback-aware.
Autonomy levels L0-L5 map to risk and approval requirements.
Mutable tool calls require idempotency metadata.
```

## M3.5 acceptance

```text
Secrets are referenced by ID, not value.
Secret Broker interface exists.
Provider Registry manifests validate.
Provider result envelopes normalize weather/news/provider responses.
No secret can enter chat, prompts, memory, logs, canonical files, or git.
```

## M4 acceptance

```text
Memory writes are source-linked, scoped, supersedable, and retrieval-aware.
Memory Retrieval V1 uses Postgres + pgvector + full-text + reranking design.
File writes use diffs/atomic operations and produce rollback metadata.
Canonical files outrank memory.
```

## M4.5 acceptance

```text
Truth Source Router schemas validate.
GroundingPolicy schema validates.
EvidenceManifest and ClaimEvidence schemas validate.
SourceConflictReport schema validates.
RetrievalLog schema validates.
Hybrid retrieval and reranking policy is documented.
Truth-governance eval specs exist.
```

## M5 acceptance

```text
Minimum Lovable Kernel completes successfully.
One real file mutation is performed through Tool Broker and File Manager.
Event Ledger, rollback, QA receipt, and source-linked memory all work.
Runtime hygiene metadata, World State/Context Budget metadata, and Evidence Manifest references are present in the trace.
```

## M6 acceptance

```text
Contract tests pass.
Shadow replay can replay the Minimum Lovable Kernel trace.
OpenWebUI/API boundary bypass tests pass.
Foundation Gate review decides whether controlled expansion can begin.
```

## Controlled expansion after gate

Only after M6 passes:

```text
M7 — Web Research V1 and Source Credibility with Evidence Manifests
M8 — Code Workspace V1 with sandboxed execution
M9 — Weather Provider V1 using free/no-key provider first
M10 — News Provider V1 with normalized events/articles
M11 — Basic Scanner Framework, read-only/digest-only
M12 — Proactive Intelligence V1, digest-first, no interrupt alerts until tuned
```

## Future control surfaces and device capabilities

These items come after runtime readiness, API/control-center contract stabilization, and web Control Center foundation. They are planning entries only in v0.14.4.

```text
Mobile Companion Contract
Device Capability Broker
Mobile Device Registry
Mobile Sensor Permission Manifest
Mobile Approval/Receipt Surface
Mobile Capture Inbox
Camera/OCR Evidence Flow
Location Privacy Flow
Push-to-Talk Voice Capture
Emergency Stop / Kill Switch
```

Mobile is a future control, approval, capture, receipt, and status surface. It is not the agent brain. Device Capability Broker work must exist before any mobile sensor integration.

## Future Codex/plugin governance

v0.14.6 adds planning and policy docs for Codex plugins and external build tools. It does not enable any plugin or external runtime.

```text
Browser + Build Web Apps — future Web Control Center work only, with approval
Build iOS Apps / XcodeBuildMCP — disabled until Mobile Companion implementation milestone
Build macOS Apps — disabled until Desktop/macOS Companion milestone
Chrome authenticated profile control — disabled unless explicitly approved
Computer Use — disabled except explicit last-resort manual QA approval
CodeRabbit/GitHub read-only — allowed for release readiness with explicit review prompt
GitHub write/release — explicit approval or direct-push rules required
Hugging Face Jobs/uploads/training — disabled
Plugin/skill installers — disabled until Skill lifecycle security exists
```

No plugin enablement should occur during M11 unless a future prompt explicitly changes the tool boundary.

## Future milestone sequence notes

```text
M11 — Runtime Foundation Readiness Gate + Manual Smoke Report Validation
Future Web Control Center — after runtime/API readiness
Future Mobile Companion — after Control Center/mobile contracts
Future real local model execution — after readiness, approval, and gate criteria
Future remote worker/tailnet execution — after planned/disabled foundation and private mesh taxonomy mature
Future scanners/proactivity/Skill Factory/self-improvement — only after their security lifecycle exists
```

Do not treat runtime readiness, UI implementation, mobile implementation, private mesh execution, scanners, Skill Factory, or self-improvement as accepted until a reviewed milestone implements and gates them.

## Out-of-sequence parked work

Any parked local Control Center work must be reintroduced through a future reviewed milestone. Parked work is not accepted baseline merely because a local branch or local tag exists.

## Later

```text
Companion proactivity
Skill Factory
Self-improving coding framework
High-autonomy external execution
Autopilot workflows
Agent interoperability
Voice/mobile UX
```

## Non-negotiable sequencing rule

Do not build scanners, companion proactivity, Skill Factory, self-improving code, autopilot workflows, provider-specific integrations, or high-autonomy external execution before the kernel, memory/files, event ledger, permission model, Tool Broker, Model Router, Cost Governor, Secret Broker, Provider Registry, rollback primitives, runtime hygiene contracts, context survival contracts, local runtime profiles, SDK/A2A adapter boundaries, observability standards mapping, Truth Source Router, Evidence Manifest, API boundary, and contract tests work.
## v0.23.0 / M19 Status

v0.23.0 implements M19 Mobile Companion Contract/API Planning only. It adds
contract models, validation helpers, docs, tests, verifier coverage, and
Foundation Gate criteria. It adds no backend API route and keeps OpenAPI path
count at `74`.

M19 marks CCC iOS and CCC Android as future planned clients only. It adds no
mobile app, Android app, iOS app, macOS app, native build workflow, OS
permission integration, mobile sensor access, mobile approval execution,
runtime execution, model/provider calls, remote execution, plugin enablement,
dependencies, OpenWebUI integration, or production Control Center authority.

Device Capability Broker contracts are required before sensors. Capture cannot
silently become memory. Phone/mobile is not the agent brain. M20 is
implemented/released as contract-only planning and validation. M21-M40 remain
planned/provisional.
