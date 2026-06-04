# 09 - Roadmap v0.39.0

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

The active accepted baseline is v0.39.0. v0.39.0 implements M35 Safe File Review Workflow Contracts as contract-only, review-only logic over already-redacted preview results. It adds redacted review packet contracts, redaction verification, exact approval binding evaluation, review-only decision envelopes, no-raw receipt plans, evaluator revalidation, tests, static verification, documentation, and Foundation Gate coverage. It adds no Control Center file review UI, approval capture, approval persistence, raw file access, raw content, full-file reads, unredacted preview, context proposal, context injection, memory writes, export, execution, backend routes, dependencies, M36 work, M37 work, M38 work, or production authority. v0.38.2 repaired M34 current-baseline labels and documentation-integrity coverage after the v0.38.1 Yellow review. v0.38.0 implements M34 Broader File Capability Review as planning, architecture review, documentation, verifier, and Foundation Gate work only. M36-M60 remain planned/provisional.

v0.25.0 adds:

- OpenWebUI bridge contract models, validation helpers, manifest builders, plan builders, and receipt planning.
- OpenWebUI bridge docs covering the chat shell contract, session/transcript refs, security model, authority boundary, non-goals, and future integration stages.
- tests and Foundation Gate coverage for M21 contract-only safety.
- static verifier coverage for forbidden OpenWebUI runtime/config/dependency/route drift.

v0.25.0 does not add OpenWebUI integration, deployment config, Docker config, OpenWebUI plugin/function/pipeline/tool/admin/auth/cookie/API key/admin token workflow, browser profile access, live OpenWebUI connection, backend API route, frontend feature, runtime execution, local LLM call, model/provider call, tool execution, memory write, file access, remote execution, browser automation, Computer Use, mobile sensor access, plugin enablement, dependency, or production authority.

v0.25.1 hardens M21 by clarifying that `raw_content_blocked` and `future_requires_contract` are blocked content-mode sentinels, not valid ref/envelope modes; allowing safe negated authority-boundary text; rejecting positive OpenWebUI authority claims; scanning `src/ultimate_ai_agent/core/openwebui_bridge/` for forbidden runtime/config fragments; and recursively rejecting forbidden OpenWebUI config/path names outside docs. OpenAPI path count remains `74`. v0.25.1 adds no OpenWebUI integration, deployment config, Docker config, OpenWebUI plugin/function/pipeline/tool/admin/auth/cookie/API key/admin token workflow, browser profile access, live OpenWebUI connection, backend API route, frontend feature, runtime execution, local LLM call, model/provider call, tool execution, memory write, file access, remote execution, browser automation, Computer Use, mobile sensor access, plugin enablement, dependency, or production authority.

v0.26.0 implements M22 Local Model Runtime Activation Contract as contract/planning/validation only. It adds metadata-only local runtime activation contracts, planned-disabled provider profiles, loopback/relative metadata endpoint policy validation, health probe plan validation, tests, static verifier coverage, Foundation Gate criteria, and docs. v0.26.1 hardens M22 verifier precision, validates metadata keys as well as values in activation policy/request/decision contracts, removes brittle local route-count unit-test ownership, and cleans duplicate M22 docs wording.

v0.27.0 implements M23 First Real Local LLM Call as a manual fixed-prompt local call path. It is dry-run by default, requires `--execute-local-call`, requires validated local approval, accepts only fixed prompt `m23_fixed_local_model_smoke_v1`, allows only loopback HTTP endpoints, uses fake transport in tests and Foundation Gate, blocks secret-like responses, stores no raw response, and records model output as non-authoritative. OpenAPI path count remains `74`. v0.27.0 adds no backend API route, runtime activation, endpoint probe, arbitrary prompt input, user-content model call, provider SDK, runtime package, OpenWebUI runtime bridge, Control Center execution control, tool execution, memory write, file write, dependency, or production authority.

v0.27.1 hardens M23 endpoint-label safety, approval validation evidence checks, response redaction/caps, CLI guardrails, policy docs, static verification, Foundation Gate criteria, and Foundation Gate report atomic write/replace safety. It adds no backend API route, runtime activation, endpoint probe, arbitrary prompt input, user-content model call, provider SDK, runtime package, OpenWebUI runtime bridge, Control Center execution control, tool execution, memory write, file write, dependency, runtime behavior expansion, or production authority.

v0.28.0 implements M24 Memory Provider Abstraction + Local Memory Store. It adds governed local memory provider contracts, local in-memory/dev store support, explicit-path stdlib SQLite support, reviewed-write validation, source priority, provenance/source/evidence/event/receipt refs, trust/confidence metadata, dedup/decay/archive planning metadata, recall-planning metadata, retention/delete/export contracts, docs, tests, verifier checks, and Foundation Gate coverage. Memory is recall, not authority. Memory is not ground truth. Canonical files, evidence manifests, receipts, Event Ledger records, and user-reviewed sources outrank memory. v0.28.0 adds no automatic memory writes, model-output writes, local LLM output writes, OpenWebUI chat memory writes, Control Center memory mutation, mobile capture writes, tool output writes, cloud memory providers, vector DB, embeddings, raw session history, context injection, backend mutation routes, dependencies, production persistence, runtime behavior expansion, or M25 claim verification. OpenAPI path count remains `74`. M25 was future at the v0.28.0 baseline.

v0.28.1 hardens M24 by repairing the package-root `MemoryWriteRequest` export to match the provider/store write path, making the legacy content-bearing request explicit as `LegacyMemoryWriteRequest`, strengthening M24 guard-field checks, clarifying that `source_refs` are required while evidence/event/receipt refs are supplemental, returning defensive copies from the in-memory store, and updating route inventory/release docs. v0.28.1 adds no automatic memory writes, model-output writes, local LLM output writes, OpenWebUI chat memory writes, Control Center memory mutation, mobile capture writes, tool output writes, cloud memory providers, vector DB, embeddings, raw session history, context injection, backend mutation routes, dependencies, production persistence, runtime behavior expansion, or M25 claim verification. OpenAPI path count remains `74`. M25 was future at the v0.28.1 baseline.

v0.28.2 removes a duplicate/conflicting v0.28.1 planned/provisional roadmap row only. It adds no code behavior change, test change, dependency, backend route, OpenAPI path count change, runtime/model/provider behavior, memory authority expansion, or M25 work. OpenAPI path count remains `74`.

v0.29.0 implements M25 Truth Source Router + Evidence Claim Checker. It adds deterministic truth source contracts, source priority ordering, claim/evidence/verification models, evidence chain validation, conflict/staleness/revocation handling, docs, tests, static verifier coverage, and Foundation Gate criteria. M25 operates locally over explicitly provided refs only. Memory is recall, not authority. Model/runtime/OpenWebUI/Control Center output cannot verify truth. Arbitrary refs cannot self-authorize claims. Verified status requires primary/source-backed evidence. v0.29.0 adds no web search, external verification, source fetching, model/provider calls, local LLM calls, retrieval/RAG/vector/embedding behavior, source crawling, memory writes, evidence mutation, backend routes, dependencies, context injection, or production authority. OpenAPI path count remains `74`. M26 was future at the v0.29.0 baseline.

v0.29.1 hardens M25 by denying unknown and arbitrary truth source refs for all verification-success statuses. Inferred unknown source kinds, unrecognized ref prefixes, and explicit `TruthSourceKind.unknown` evidence cannot produce `source_linked`, `evidence_supported`, or `verified_by_primary_source`. Claims cannot self-verify. Recognized primary/source-backed evidence still supports verified status. v0.29.1 adds regression tests, static verifier checks, docs, and Foundation Gate coverage for those denial paths. It adds no web search, external verification, source fetching, model/provider calls, local LLM calls, retrieval/RAG/vector/embedding behavior, source crawling, memory writes, evidence mutation, backend routes, dependencies, M26 context-pack builder, context injection, or production authority. OpenAPI path count remains `74`. M26 was future at the v0.29.1 baseline.

v0.29.2 hardens local-dev API authority and raw preview safety. Test-prefixed `approval_test_*` refs are not fallback authority in Tool Broker/kernel mutation paths. Public `/kernel/tasks/run` local-dev mutation requests are dry-run-only. Public file read previews are metadata-only by default and mark raw content omitted. API safe messages do not echo raw exception strings or hostile invalid input. Direct truth memory/model authority helpers fail closed. v0.29.2 adds tests, static verifier checks, docs, and Foundation Gate coverage for those boundaries. It adds no web search, external verification, source fetching, model/provider calls, local LLM calls, retrieval/RAG/vector/embedding behavior, source crawling, memory writes, evidence mutation, backend routes, dependencies, M26 context-pack builder, context injection, or production authority. OpenAPI path count remains `74`. M26 was future at the v0.29.2 baseline.

v0.29.3 reorganizes documentation structure and repository root hygiene. Historical release/import/master-plan packets move under `docs/archive/releases/`, miscellaneous retired root planning packets move under `docs/archive/retired_plans/`, docs archive entrypoints are added, and active indexes/verifiers distinguish active docs from historical archive docs. v0.29.3 adds no runtime behavior, backend route, frontend feature, dependency, model/provider call, memory write, tool execution, security architecture change, M26 Grounded Recall Router, Context Pack Builder, or production authority. OpenAPI path count remains `74`. M26 was future at the v0.29.3 baseline.

v0.29.4 repairs the v0.29.3 documentation archive cleanup by archiving active-looking historical version verifiers, removing stale Ruff excludes for retired verifier paths, adding a self-maintaining documentation organization policy, updating active indexes/release docs, and hardening documentation-integrity checks so active validation cannot depend on moved root historical release artifacts. v0.29.4 adds no runtime behavior, backend route, frontend feature, dependency, model/provider call, memory write, tool execution, security architecture change, M26 Grounded Recall Router, Context Pack Builder, or production authority. OpenAPI path count remains `74`. M26 was future at the v0.29.4 baseline.

v0.29.5 accepts the pushed documentation organization policy wording cleanup from `374bb1e`. It removes duplicated wording only and adds no runtime behavior, backend route, frontend feature, dependency, model/provider call, memory write, tool execution, security architecture change, M26 Grounded Recall Router, Context Pack Builder, or production authority. OpenAPI path count remains `74`. M26 was future at the v0.29.5 baseline.

v0.30.0 implements M26 Grounded Recall Router + Evidence-Linked Context Pack Builder. It adds deterministic local recall/context-pack contracts over provided safe candidates, source priority that keeps canonical/evidence/receipt/event/user-reviewed refs above memory, exclusion of unknown/arbitrary/stale/conflicted/revoked/deleted/superseded/model/runtime/OpenWebUI/raw/secret candidates, safe summary-only context packs, docs, tests, static verifier coverage, and Foundation Gate criteria. v0.30.0 adds no backend routes, frontend features, vector search, embeddings, semantic search, RAG ingestion, web search, external retrieval, source crawling, arbitrary file reads, model/provider calls, local LLM calls, memory writes, evidence mutation, Event Ledger mutation, context injection runtime, OpenWebUI runtime bridge, dependencies, tool execution, or production authority. OpenAPI path count remains `74`. M27 remains planned/provisional.

v0.30.1 hardens M26 recall source identity validation. It enforces consistency between source_ref prefixes and declared source_kind, denies mismatched memory/model/runtime/OpenWebUI refs, prevents caller-declared source_kind from upgrading source priority, adds regression tests and Foundation Gate/static verifier coverage, and preserves safe canonical/evidence/receipt/event source selection. v0.30.1 adds no backend routes, frontend features, vector search, embeddings, semantic search, RAG ingestion, web search, external retrieval, source crawling, model/provider calls, local LLM calls, memory writes, context injection runtime, dependencies, tool execution, M27 work, or production authority. OpenAPI path count remains `74`. M27 remains planned/provisional.

v0.31.1 is a docs-only baseline normalization for the GitHub README polish commit. v0.31.0 implements M27 Tool Broker v2 + Safe Tool Intent Contracts. It adds deterministic local validation-only contracts for tool targets, input boundaries, catalog entries, tool intents, decisions, manifests, and non-executing receipt plans. M27 allows safe metadata-only preview decisions while denying unknown tools, target mismatches, side effects, approval refs as authority, context packs as authority, caller risk downgrades, hidden side effects, raw content, secret-like content, model output, runtime output, and OpenWebUI output. v0.31.1 adds no backend routes, frontend features, real tool execution, action execution, shell execution, file mutation, memory writes, Event Ledger mutation, external network calls, web search, browser automation, Computer Use, plugin enablement, model/provider calls, local LLM calls, retrieval/RAG/vector/embedding behavior, context injection runtime, dependencies, M28 work, or production authority. OpenAPI path count remains `74`.

v0.32.0 implements M28 Approval Authority v2 + Action Policy Expansion. It adds non-executing approval authority contracts, action policy contracts, actor/action/resource/scope binding, expiry/revocation/replay protection, approval_ref and approval_test_ denial, consent_ref denial, wildcard grant denial, action risk and side-effect policy, approval/action policy decisions, non-authoritative receipt plans, docs, tests, static verifier coverage, and Foundation Gate coverage. M28 allows safe no-effect/read-metadata policy decisions with `execution_authorized=False` and `execution_performed=False`. v0.32.0 adds no backend routes, frontend features, action execution, real tool execution, shell/subprocess execution, file mutation, memory writes, Event Ledger mutation, external network calls, web search, browser automation, mobile/device access, remote execution, Computer Use, plugin enablement, model/provider calls, local LLM calls, retrieval/RAG/vector/embedding behavior, context injection runtime, dependencies, M29 work, or production authority. OpenAPI path count remains `74`. Later roadmap currentness is governed by the active sequence below.

v0.33.0 implements M29 Agent Task Planning Engine. It adds deterministic local task goal, task step, task plan, dependency graph, input boundary, risk/authority, decision envelope, and receipt plan contracts. M29 validates plans for human review only, denies execution requests, auto-run, scheduler requests, raw/secret inputs, non-authoritative model/memory/context-pack/tool-intent/approval refs, caller risk downgrades, effectful or executing steps, duplicate steps, missing dependencies, and dependency cycles. v0.33.0 adds no backend routes, frontend features, task execution, scheduler runtime, action execution, real tool execution, shell/subprocess execution, file mutation, memory writes, Event Ledger mutation, external network calls, web search, browser automation, mobile/device access, remote execution, Computer Use, plugin enablement, model/provider calls, local LLM calls, retrieval/RAG/vector/embedding behavior, context injection runtime, dependencies, M30 work, or production authority. OpenAPI path count remains `74`. At the v0.33.0 baseline, M30-M40 remained planned/provisional.

v0.33.1 hardens M29 Agent Task Planning Engine. It strengthens dependency graph validation, duplicate/missing step denial, self/indirect cycle detection, derived risk enforcement, hidden side-effect denial, authority-boundary checks, evaluator revalidation, static verification, Foundation Gate coverage, and no-execution invariants. v0.33.1 adds no backend routes, frontend features, task execution, scheduler runtime, background worker, action execution, real tool execution, shell/subprocess execution, file mutation, memory writes, Event Ledger mutation, external network calls, web search, browser automation, mobile/device access, remote execution, Computer Use, plugin enablement, model/provider calls, local LLM calls, retrieval/RAG/vector/embedding behavior, context injection runtime, dependencies, M30 work, or production authority. OpenAPI path count remains `74`. At the v0.33.1 baseline, M30-M40 remained planned/provisional.

v0.34.0 implements M30 Multi-Step Execution Framework. It adds deterministic local execution run, step, transition, manifest, validation, decision, replay-protection, dependency progression, and receipt-plan contracts for no-effect state advancement only. M30 denies execution requests, auto-run, scheduler/background worker requests, raw/secret inputs, non-authoritative model/runtime/OpenWebUI/memory/context-pack/tool-intent/approval/Control Center refs, replay-key reuse, duplicate steps, missing dependencies, and dependency cycles. v0.34.0 adds no backend routes, frontend features, real task execution, scheduler runtime, background worker, autonomous loop, action execution, real tool execution, shell/subprocess execution, file mutation, memory writes, Event Ledger mutation, external network calls, web search, browser automation, mobile/device access, remote execution, Computer Use, plugin enablement, model/provider calls, local LLM calls, retrieval/RAG/vector/embedding behavior, context injection runtime, dependencies, M31 work, or production authority. OpenAPI path count remains `74`. M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool, M32 is implemented/released by v0.36.0 as Safe Local Filesystem Metadata Tool, and M33 is implemented/released by v0.37.0 as First Safe Local File Read Proposal, Redacted Preview Only. M36-M60 remain planned/provisional.

v0.34.1 hardens M30 Multi-Step Execution Framework. It strengthens invalid run/step transition denial, ready-only no-effect step completion, blocked/already-completed step denial, incomplete run finalization denial, replay-key and transition-id replay protection, hidden side-effect metadata denial, side-effect execution flag denial, evaluator revalidation, static verification, Foundation Gate coverage, and no-side-effect invariants. v0.34.1 adds no backend routes, frontend features, real task execution, scheduler runtime, background worker, autonomous loop, action execution, real tool execution, shell/subprocess execution, file mutation, memory writes, Event Ledger mutation, external network calls, web search, browser automation, mobile/device access, remote execution, Computer Use, plugin enablement, model/provider calls, local LLM calls, retrieval/RAG/vector/embedding behavior, context injection runtime, dependencies, M31 work, or production authority. OpenAPI path count remains `74`. M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool, M32 is implemented/released by v0.36.0 as Safe Local Filesystem Metadata Tool, and M33 is implemented/released by v0.37.0 as First Safe Local File Read Proposal, Redacted Preview Only. M36-M60 remain planned/provisional.

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
- `docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md`.
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

## Accepted baseline through v0.32.0

The active accepted baseline includes foundation modules through M10.5 plus documentation integrity synchronization, Codex plugin/external tooling governance, M11 runtime readiness/report validation, M12 Control Center backend contract/API foundation, M13 Web Control Center read-only frontend shell with CI/static/browser-readiness hardening, the v0.17.5 roadmap charter freeze, M14 local backend connection stabilization and safety hardening, v0.18.2 design governance, v0.18.3 OpenWebUI/CCC client strategy clarification, v0.18.4 post-M20 roadmap projection, v0.19.0 M15 Approval Queue + Receipt/Event Viewer UI, v0.19.1 M15 Approval/Receipt UI safety hardening, v0.20.0 M16 Event Timeline + Run/Receipt Trace Viewer, v0.20.1 M16 trace/redaction safety hardening, v0.21.0 M17 Evidence/File/Memory Viewer, v0.21.1 M17 safety hardening, v0.21.2 developer environment command normalization, v0.22.0 M18 Local Runtime Status + Manual Smoke Control Surface, v0.22.1 roadmap status label cleanup, v0.23.0 M19 Mobile Companion Contract/API Planning, v0.23.1 M19 roadmap/mobile-contract safety cleanup, v0.24.0 M20 Device Capability Broker Contract, v0.24.1 M20 safety hardening, v0.25.0 M21 OpenWebUI Bridge + Chat Shell Integration Contract, v0.25.1 M21 OpenWebUI bridge contract safety hardening, v0.26.0 M22 Local Model Runtime Activation Contract, v0.26.1 M22 safety hardening, v0.27.0 M23 First Real Local LLM Call, v0.27.1 M23 local call safety hardening, v0.28.0 M24 Memory Provider Abstraction + Local Memory Store, v0.28.1 M24 contract repair and memory safety hardening, v0.28.2 roadmap row cleanup, v0.29.0 M25 Truth Source Router + Evidence Claim Checker, v0.29.1 M25 unknown/arbitrary truth ref denial hardening, v0.29.2 local-dev API authority/raw preview hardening, v0.29.4 documentation archive reference repair, v0.29.5 documentation organization policy polish, v0.30.0 M26 Grounded Recall Router + Evidence-Linked Context Pack Builder, v0.30.1 M26 recall source identity hardening, v0.31.0 M27 Tool Broker v2 + Safe Tool Intent Contracts, v0.31.1 GitHub README Polish Baseline Normalization, and v0.32.0 M28 Approval Authority v2 + Action Policy Expansion. v0.29.3 remains preserved as historical documentation organization work superseded by v0.29.4 after review. v0.17.4 polished local shell reviewability and browser smoke reporting only; it did not start M14, add backend API paths, add dependencies, add production Control Center authority, or add execution capability.

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
v0.25.1 — M21 OpenWebUI Bridge Contract Safety Hardening
v0.26.0 — M22 Local Model Runtime Activation Contract
v0.26.1 — M22 Safety Hardening
v0.27.0 — M23 First Real Local LLM Call, Non-Tool, Non-Authoritative
v0.27.1 — M23 Local LLM Call Safety Hardening
v0.28.0 — M24 Memory Provider Abstraction + Local Memory Store
v0.28.1 — M24 Contract Repair + Memory Safety Hardening
v0.28.2 — M24 Duplicate Roadmap Row Cleanup
v0.29.0 — M25 Truth Source Router + Evidence Claim Checker
v0.29.1 — M25 Reject Unknown Truth Refs Hardening
v0.29.2 — M25 Local Dev API Authority + Raw Preview Safety Hardening
v0.29.3 — Documentation Archive Structure + Active/Historical Classification
v0.29.4 — Documentation Archive Reference Repair + Self-Maintaining Docs Policy
v0.29.5 — Documentation Organization Policy Polish
v0.30.0 / M26 — Grounded Recall Router + Evidence-Linked Context Pack Builder
v0.30.1 / M26 hardening — Recall Source Ref / Source Kind Consistency
v0.31.0 / M27 — Tool Broker v2 + Safe Tool Intent Contracts

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

v0.18.0 and v0.18.1 have implemented and hardened M14 from that sequence. v0.18.2 has implemented the Open Design governance milestone. v0.18.3 has implemented OpenWebUI and CCC Client Strategy clarification. v0.18.4 has implemented post-M20 roadmap projection docs. v0.19.0 has implemented M15 frontend-only Approval Queue + Receipt/Event Viewer UI. v0.19.1 has hardened M15 Approval/Receipt UI safety. v0.20.0 has implemented M16 frontend-only Event Timeline + Run/Receipt Trace Viewer. v0.20.1 has hardened M16 trace/redaction safety. v0.21.0 has implemented M17 frontend-only Evidence/File/Memory Viewer. v0.21.1 has hardened M17 evidence/file/memory viewer safety. v0.21.2 has normalized developer environment commands. v0.22.0 has implemented M18 frontend-only Local Runtime Status + Manual Smoke Control Surface. v0.22.1 has cleaned up roadmap status labels only. v0.23.0 has implemented/released M19 Mobile Companion Contract/API Planning only. v0.23.1 has hardened M19 roadmap currentness and mobile contract safety tests only. v0.24.0 has implemented/released M20 Device Capability Broker Contract only. v0.24.1 has hardened M20 Device Capability Broker Contract safety only. v0.25.0 has implemented/released M21 OpenWebUI Bridge + Chat Shell Integration Contract as contract/planning/validation only. v0.25.1 has hardened M21 OpenWebUI bridge contract safety only. v0.26.0 has implemented/released M22 Local Model Runtime Activation Contract as contract/planning/validation only. v0.26.1 has hardened M22 verifier precision and metadata key secret hygiene only. v0.27.0 has implemented/released M23 First Real Local LLM Call as manual fixed-prompt local call only. v0.27.1 has hardened M23 local call safety only. v0.28.0 has implemented/released M24 Memory Provider Abstraction + Local Memory Store as governed local memory foundation. v0.28.1 has repaired and hardened the M24 memory contract. v0.28.2 has cleaned up the duplicate roadmap row only. v0.29.0 has implemented/released M25 Truth Source Router + Evidence Claim Checker as deterministic local truth/evidence contracts. v0.29.1, v0.29.2, and v0.29.4 harden the pre-M26 baseline; v0.29.3 remains preserved as historical documentation organization work superseded by v0.29.4. v0.30.0 has implemented/released M26 Grounded Recall Router + Evidence-Linked Context Pack Builder as deterministic local contracts. v0.31.0 has implemented/released M27 Tool Broker v2 + Safe Tool Intent Contracts as validation-only contracts. v0.31.1 normalizes the GitHub README polish commit into a docs-only baseline. v0.32.0 has implemented/released M28 Approval Authority v2 + Action Policy Expansion as policy-only contracts. v0.33.0 has implemented/released M29 Agent Task Planning Engine as review-only planning contracts. v0.34.0 has implemented/released M30 Multi-Step Execution Framework as state-machine-only contracts. v0.35.0 has implemented/released M31 Real Tool Runtime Adapter, Single Safe No-Op Tool. v0.36.0 has implemented/released M32 Safe Local Filesystem Metadata Tool, v0.36.1 hardens M32 path safety, v0.37.0 has implemented/released M33 First Safe Local File Read Proposal, Redacted Preview Only, v0.37.1 hardens redacted preview safety, v0.37.2 adds local developer launcher tooling only, v0.37.3 repairs active M34 roadmap label alignment, v0.37.4 supersedes the post-M33 roadmap through M60, and v0.38.0 implements M34 Broader File Capability Review as planning/docs/verifier only. M36-M60 remain planned/provisional until implemented by dedicated reviewed roadmap patches.

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
v0.26.0 / M22 — Local Model Runtime Activation Contract, implemented/released contract-only
v0.27.0 / M23 — First Real Local LLM Call, Non-Tool, Non-Authoritative, implemented/released
v0.27.1 / M23 hardening — Local LLM Call Safety Hardening, implemented/released
v0.28.0 / M24 — Memory Provider Abstraction + Local Memory Store, implemented/released
v0.29.0 / M25 — Truth Source Router + Evidence Claim Checker, implemented/released contract-only
v0.29.1 / M25 hardening — Reject Unknown Truth Refs, implemented/released
v0.29.2 / M25 hardening — Local Dev API Authority + Raw Preview Safety, implemented/released
v0.29.3 — Documentation Archive Structure + Active/Historical Classification, implemented/released docs-only
v0.29.4 — Documentation Archive Reference Repair + Self-Maintaining Docs Policy, implemented/released docs-only
v0.29.5 — Documentation Organization Policy Polish, implemented/released docs-only
v0.30.0 / M26 — Grounded Recall Router + Evidence-Linked Context Pack Builder, implemented/released contract-only
v0.30.1 / M26 hardening — Recall Source Ref / Source Kind Consistency, implemented/released
v0.31.0 / M27 — Tool Broker v2 + Safe Tool Intent Contracts, implemented/released contract-only
v0.31.1 — GitHub README Polish Baseline Normalization, implemented/released docs-only
v0.32.0 / M28 — Approval Authority v2 + Action Policy Expansion, implemented/released contract-only
v0.32.1 / M28 hardening — Evaluator Revalidation for Raw/Secret Action Inputs, implemented/released
v0.33.0 / M29 — Agent Task Planning Engine, implemented/released contract-only
v0.33.1 / M29 hardening — Task Plan Dependency, Risk, and No-Execution Safety, implemented/released
v0.34.0 / M30 — Multi-Step Execution Framework, implemented/released contract-only
v0.34.1 — M30 hardening: Execution State Machine, Replay, and No-Side-Effect Safety, implemented/released
v0.35.0 / M31 — Real Tool Runtime Adapter, Single Safe No-Op Tool, implemented/released
v0.35.1 / M31 hardening — No-Op Tool Runtime Adapter Safety, implemented/released
v0.36.0 / M32 — Safe Local Filesystem Metadata Tool, implemented/released
v0.36.1 / M32 hardening — Filesystem Metadata Path Safety, implemented/released
v0.37.0 / M33 — First Safe Local File Read Proposal, Redacted Preview Only, implemented/released
v0.37.1 / M33 hardening — Redacted File Preview Safety, implemented/released
v0.37.2 — Local Developer Launcher + Desktop Shortcut, implemented/released tooling-only
v0.37.3 — Roadmap Label Alignment + Documentation Integrity Guard, implemented/released docs/verifier-only
v0.37.4 — Roadmap Supersession Through M60 + Documentation Integrity Guard, implemented/released docs/verifier-only
v0.38.0 / M34 — Broader File Capability Review, implemented/released planning/docs/verifier only
v0.38.1 — M34 hardening: File Capability Review Boundary Clarity, reviewed Yellow and superseded by v0.38.2
v0.38.2 — M34 current baseline label + documentation integrity repair, implemented/released docs/verifier-only
v0.39.0 / M35 — Safe File Review Workflow Contracts, implemented/released contract-only
v0.40.0 / M36 — CCC File Review Surface, Review-Only, planned/provisional
v0.41.0 / M37 — Review Approval Capture, Review-Only Persistence, planned/provisional
v0.42.0 / M38 — Safe Context Proposal From Approved Review, planned/provisional
v0.43.0 / M39 — CCC Context Proposal Surface, planned/provisional
v0.44.0 / M40 — Context Handoff Approval, No Injection, planned/provisional
v0.45.0 / M41 — Local Prototype Safety Freeze, planned/provisional
v0.46.0 / M42 — Mobile Companion Product Contract Refresh, planned/provisional
v0.47.0 / M43 — Mobile API Boundary, Read-Only, planned/provisional
v0.48.0 / M44 — CCC iOS Skeleton, No Authority, planned/provisional
v0.49.0 / M45 — CCC iOS Local Read-Only Connection, planned/provisional
v0.50.0 / M46 — iOS Review/Receipt Read-Only Surfaces, planned/provisional
v0.51.0 / M47 — TestFlight Pipeline, Internal Only, planned/provisional
v0.52.0 / M48 — First Internal TestFlight Build, planned/provisional
v0.53.0 / M49 — Mobile Review Approval Capture, planned/provisional
v0.54.0 / M50 — Mobile Approval Audit Hardening, planned/provisional
v0.55.0 / M51 — OpenWebUI Bridge Adapter Pilot, planned/provisional
v0.56.0 / M52 — OpenWebUI Safe Conversation Surface, planned/provisional
v0.57.0 / M53 — Controlled Tool Expansion Review, planned/provisional
v0.58.0 / M54 — Safe Media Metadata Inspector, planned/provisional
v0.59.0 / M55 — Redacted Observability Export, planned/provisional
v0.60.0 / M56 — Agent Eval Regression Harness, planned/provisional
v0.61.0 / M57 — Runtime Sandbox Architecture Review, planned/provisional
v0.62.0 / M58 — Dry-Run Execution Audit Harness, planned/provisional
v0.63.0 / M59 — Public GitHub Readiness, planned/provisional
v0.64.0 / M60 — Local Developer Beta Freeze, planned/provisional
```

M14 is not local browser smoke / UX polish. That work was v0.17.4. M15 is the first planned approval queue plus receipt/event viewer UI milestone, and it remains read-only/preview-only unless a future backend contract explicitly changes that boundary.

Post-M20 source-of-truth docs:

- `docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md`.
- `docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md`.
- `docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md`.
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
