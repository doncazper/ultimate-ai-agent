# M21-M40 Capability Charters

Status: Active roadmap projection maintained through v0.26.1. M21 and M22 are implemented/released contract-only; M22 is safety-hardened; M23-M40 remain planned/provisional.

These charters define capability layers after M20. v0.25.0 implements M21 as contract/planning/validation only. v0.26.0 implements M22 as contract/planning/validation only, and v0.26.1 hardens M22 verifier precision plus metadata key secret hygiene only. M23-M40 are still future capability layers. Every milestone requires its own implementation prompt, review prompt, hardening expectation, and validation evidence before release.

## Shared Rules

- Python Agent Core remains the brain.
- OpenWebUI is the preferred conversational web shell.
- CCC is the user-control and governance client family.
- Model output is never source of truth.
- Memory is recall, not authority.
- External tools, plugins, standards, sandboxes, browsers, devices, and remote workers are not authority.
- No milestone may bypass Approval Authority, Consent Ledger, Tool Broker, Event Ledger, Secret Broker, Redaction, Foundation Gate, or verifier scripts.
- High-risk capability must first appear as docs, contracts, policy, dry-run, or validation-only before implementation.

## v0.25.0 / M21 - OpenWebUI Bridge + Chat Shell Integration Contract

Status: implemented/released contract-only.

Purpose: Define how OpenWebUI will talk to the Python Agent Core without becoming the brain.

Allowed scope:

- OpenWebUI bridge docs.
- chat ingress/egress contracts.
- session refs.
- safe transcript refs.
- validation helpers and Foundation Gate coverage.

Must not add:

- real OpenWebUI deployment.
- Docker Compose.
- OpenWebUI plugin/tool bridge.
- model execution.
- tool execution.
- memory writes.
- external exposure.
- authority bypass.

Dependencies: v0.18.3 OpenWebUI/CCC strategy, stable API/OpenAPI contracts, Python Agent Core authority contract.

Acceptance criteria:

- OpenWebUI remains the preferred conversational shell.
- Agent Core remains authority.
- no bypass of Approval Authority, Consent Ledger, Tool Broker, Event Ledger, Secret Broker, or Foundation Gate.
- no OpenWebUI integration, deployment config, backend route, frontend feature, runtime execution, model/provider call, tool execution, memory write, file access, dependency, or production authority.

Review prompt required: yes.

Hardening expectation: M21 hardening patch before any actual OpenWebUI integration.

Source-of-truth docs: `docs/ui/OPENWEBUI_AND_CCC_STRATEGY.md`, `docs/ui/OPENWEBUI_INTEGRATION_ROADMAP.md`, `docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md`.

Notes: M21 is contract-only. OpenWebUI integration remains not implemented until a later reviewed milestone explicitly authorizes it.

## v0.26.0 / M22 - Local Model Runtime Activation Contract

Status: implemented/released contract-only.

Purpose: Define how local runtimes like Ollama, llama.cpp, MLX, vLLM, and LM Studio can be represented safely.

Allowed scope:

- local runtime provider profiles.
- loopback/relative endpoint metadata policy.
- activation policy, request, and decision contracts.
- runtime health probe plan validation.
- tests, docs, static verifier coverage, and Foundation Gate criteria.

Must not add:

- cloud provider calls.
- external model APIs.
- runtime activation.
- endpoint probes.
- real local model calls.
- provider SDK imports.
- runtime package imports.
- tool use.
- memory writes.
- user-content execution.
- production model authority.

Dependencies: M21 contracts, runtime readiness docs, local-only endpoint policy.

Acceptance criteria: local runtime profiles are metadata/validation-only and cannot execute user content, tools, or memory writes. No model was called, no runtime was activated, no endpoint was contacted, and OpenAPI path count remains `74`.

Review prompt required: yes.

Hardening expectation: local endpoint, timeout, and secret handling hardening before M23.

Source-of-truth docs: `docs/runtime/LOCAL_MODEL_RUNTIME_ACTIVATION_CONTRACT.md`, `docs/runtime/LOCAL_RUNTIME_PROVIDER_PROFILES.md`, `docs/runtime/LOCAL_RUNTIME_ENDPOINT_POLICY.md`, `docs/runtime/LOCAL_RUNTIME_HEALTH_PROBE_PLAN.md`, `docs/runtime/LOCAL_RUNTIME_ACTIVATION_SECURITY_MODEL.md`, `docs/runtime/LOCAL_RUNTIME_ACTIVATION_NON_GOALS.md`, `docs/runtime/LOCAL_RUNTIME_M22_TO_M23_BOUNDARY.md`, `docs/runtime/RUNTIME_READINESS.md`, `docs/runtime/RUNTIME_CAPABILITY_MATRIX.md`, `docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md`.

Notes: Free/open-source/self-hosted local runtimes should be evaluated first where practical. M23 remains planned/provisional.

## v0.27.0 / M23 - First Real Local LLM Call, Non-Tool, Non-Authoritative

Status: planned/provisional.

Purpose: Allow the first tightly bounded local LLM inference path.

Allowed scope:

- explicit local-only model call.
- no tools.
- no memory writes.
- no external network.
- no secrets.
- fixed or sanitized prompt envelope.
- non-authoritative response.
- Event Ledger receipt.

Must not add:

- tool calls.
- autonomous action.
- memory mutation.
- provider/cloud calls.
- freeform OpenWebUI bridge.

Dependencies: M22 local runtime activation contract and local-only guard.

Acceptance criteria: first local LLM call is local-only, non-authoritative, receipt-backed, and cannot mutate state or execute tools.

Review prompt required: yes.

Hardening expectation: v0.27.1 Local LLM Call Hardening is required before memory or tool expansion.

Source-of-truth docs: `docs/runtime/local_loopback_model_runtime.md`, `docs/runtime/RUNTIME_READINESS.md`, `docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md`.

Notes: Model output remains advisory and must be labeled non-authoritative.

## v0.27.1 - Local LLM Call Hardening

Status: planned/provisional.

Purpose: Harden the first bounded local LLM path before the next capability jump.

Allowed scope:

- prompt redaction.
- response labeling.
- timeout/error handling.
- non-authoritative output checks.
- no secret echo.
- no tool-call leakage.

Must not add:

- new tools.
- memory writes.
- cloud providers.
- OpenWebUI freeform bridge.
- autonomous actions.

Dependencies: M23.

Acceptance criteria: local LLM responses are redacted, labeled, timeout-safe, non-authoritative, and cannot leak tool-call authority.

Review prompt required: yes.

Hardening expectation: this is the hardening patch for M23.

Source-of-truth docs: `docs/runtime/RUNTIME_READINESS.md`, `docs/testing/test_strategy_v0.md`.

Notes: This patch must remain focused on hardening.

## v0.28.0 / M24 - Memory Provider Abstraction + Local Memory Store

Status: planned/provisional.

Purpose: Introduce real memory storage carefully.

Allowed scope:

- MemoryProvider interface.
- local SQLite/dev memory store.
- memory record lifecycle.
- memory review states.
- user-reviewed writes.
- delete/export contracts.

Must not add:

- automatic memory writes.
- unreviewed personal profiling.
- cloud memory providers.
- vector DB dependency unless explicitly approved.

Dependencies: M23 hardening, memory policy, truth/evidence boundaries.

Acceptance criteria: memory writes require review, provenance, delete/export paths, and no secret storage.

Review prompt required: yes.

Hardening expectation: v0.28.1 Memory Safety Hardening before truth/evidence expansion.

Source-of-truth docs: `docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md`, `src/ultimate_ai_agent/core/memory/`.

Notes: Memory is recall, not authority.

## v0.28.1 - Memory Safety Hardening

Status: planned/provisional.

Purpose: Harden memory provenance, deletion, and conflict behavior.

Allowed scope:

- memory provenance.
- deletion/export checks.
- no secret storage.
- no auto-write.
- stale/conflicting memory behavior.
- memory does not outrank canonical sources.

Must not add:

- automatic memory writes.
- cloud memory.
- profiling.
- vector DB dependency.

Dependencies: M24.

Acceptance criteria: memory records are provenance-backed, deletable/exportable, secret-safe, and lower authority than canonical sources.

Review prompt required: yes.

Hardening expectation: this is the hardening patch for M24.

Source-of-truth docs: `docs/testing/test_strategy_v0.md`, `src/ultimate_ai_agent/core/memory/`.

Notes: Conflicts must be visible and reviewable.

## v0.29.0 / M25 - Truth Source Router + Evidence Claim Checker

Status: planned/provisional.

Purpose: Make model claims inspectable.

Allowed scope:

- claim/evidence linking.
- truth-source routing UI.
- evidence refs.
- source summaries.
- claim confidence/review status.

Must not add:

- automated truth claims as authority.
- external web search unless separately gated.
- unreviewed source ingestion.

Dependencies: M24 memory safety and existing truth/evidence contracts.

Acceptance criteria: claims link to evidence refs and confidence/review status without making model output authoritative.

Review prompt required: yes.

Hardening expectation: claim-source mismatch and stale-source hardening before tool sandbox work.

Source-of-truth docs: `docs/canonical/09_roadmap.md`, `src/ultimate_ai_agent/core/truth/`.

Notes: Evidence supports review; it does not become autonomous authority.

## v0.30.0 / M26 - Tool Execution Sandbox Contract, Dry-Run Only

Status: planned/provisional.

Purpose: Define tool execution sandbox contracts before any execution.

Allowed scope:

- sandbox policy contracts.
- filesystem/network/credential scopes.
- dry-run tool envelopes.
- artifact manifests.
- approval requirements.

Must not add:

- real shell execution.
- real browser automation.
- real file writes.
- real external actions.

Dependencies: M25 claim/evidence governance and Tool Broker policy.

Acceptance criteria: tool requests can be described, scoped, risk-rated, and previewed without executing.

Review prompt required: yes.

Hardening expectation: sandbox policy hardening before MCP/skills trust registry.

Source-of-truth docs: `docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md`, `src/ultimate_ai_agent/core/tools/`.

Notes: M26 is dry-run only.

## v0.31.0 / M27 - MCP / Agent Skills / AGENTS.md Trust Registry, Quarantine-Only

Status: planned/provisional.

Purpose: Establish trust lifecycle for MCP, Agent Skills, and AGENTS.md before runtime use.

Allowed scope:

- MCP server manifests.
- Agent Skills / SKILL.md metadata.
- AGENTS.md workspace instruction model.
- quarantine state.
- static policy checks.
- permission manifests.

Must not add:

- runtime MCP calls.
- skill execution.
- auto-install.
- marketplace installs.
- credential access.

Dependencies: M26 sandbox contracts and Codex plugin governance docs.

Acceptance criteria: MCP, Agent Skills, and AGENTS.md entries can be inventoried and quarantined without runtime execution.

Review prompt required: yes.

Hardening expectation: trust lifecycle hardening before sandbox backend abstraction.

Source-of-truth docs: `docs/tooling/CODEX_PLUGIN_RISK_POLICY.md`, `docs/canonical/66_external_tooling_and_codex_plugin_governance.md`.

Notes: Quarantine-only means no runtime trust is granted.

## v0.32.0 / M28 - Local Sandbox Backend Abstraction

Status: planned/provisional.

Purpose: Define backend abstraction for future sandbox execution without executing.

Allowed scope:

- ExecutionBackend interface.
- local-docker planned metadata.
- daytona/e2b/sandbox0 planned metadata.
- workspace policies.
- network policies.
- artifact refs.

Must not add:

- real Docker execution.
- cloud sandbox calls.
- SSH execution.
- browser/computer-use execution.

Dependencies: M27 trust registry and M26 sandbox contracts.

Acceptance criteria: sandbox backends are represented as planned metadata and policy contracts only.

Review prompt required: yes.

Hardening expectation: backend isolation and artifact-policy hardening before dry-run tool previews.

Source-of-truth docs: `docs/roadmap/ECOSYSTEM_WATCHLIST.md`, `docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md`.

Notes: No sandbox provider is integrated by this charter.

## v0.33.0 / M29 - First Low-Risk Tool Dry-Run + Approval Preview

Status: planned/provisional.

Purpose: Produce first low-risk tool dry-run previews and approval requests.

Allowed scope:

- tool dry-run previews.
- diff previews.
- approval request generation.
- receipt previews.

Must not add:

- real writes.
- real sends.
- real shell commands.
- real external API mutation.

Dependencies: M28 sandbox backend abstraction and Approval Authority contracts.

Acceptance criteria: low-risk tool plans can produce diffs, approval requests, and receipt previews without execution.

Review prompt required: yes.

Hardening expectation: dry-run correctness and approval preview hardening before local execution.

Source-of-truth docs: `src/ultimate_ai_agent/core/tools/`, `src/ultimate_ai_agent/core/approvals/`.

Notes: Dry-run previews are non-authoritative until approved.

## v0.34.0 / M30 - First Approved Low-Risk Local Tool Execution

Status: planned/provisional.

Purpose: Allow the first explicitly approved low-risk local tool execution.

Allowed scope:

- limited local tool.
- explicit approval.
- rollback path.
- event receipt.
- artifact diff.

Must not add:

- network calls.
- credential use.
- irreversible actions.
- browser/computer-use.
- remote execution.

Dependencies: M29 dry-run approval preview and sandbox hardening.

Acceptance criteria: a single low-risk local tool can execute only with explicit approval, event receipt, and rollback/artifact diff where practical.

Review prompt required: yes.

Hardening expectation: post-execution receipt, rollback, and injection hardening before native client contracts.

Source-of-truth docs: `src/ultimate_ai_agent/core/tools/`, `src/ultimate_ai_agent/core/ledger/`.

Notes: This is the first real local tool execution milestone, not broad tool enablement.

## v0.35.0 / M31 - CCC Native Client Contract: iOS / Android / macOS

Status: planned/provisional.

Purpose: Define CCC native client contracts for iOS, Android, and macOS.

Allowed scope:

- CCC iOS contract.
- CCC Android contract.
- CCC macOS contract.
- shared API contract.
- pairing/trust handshake planning.
- native permissions policy.

Must not add:

- iOS app.
- Android app.
- macOS app.
- React Native.
- Flutter.
- Swift/Kotlin.
- Gradle/Xcode.
- mobile sensor access.
- signing/keystore/provisioning.

Dependencies: M30 low-risk local tool hardening and v0.18.3 CCC native client strategy.

Acceptance criteria: native client contracts define control-surface roles without app implementation, native build tooling, OS permissions, sensors, or signing workflows.

Review prompt required: yes.

Hardening expectation: native permissions and API boundary hardening before device pairing.

Source-of-truth docs: `docs/ui/CCC_NATIVE_CLIENT_STRATEGY.md`, `docs/canonical/64_mobile_companion_and_device_capability_broker.md`.

Notes: CCC native clients are control surfaces, not the agent brain.

## v0.36.0 / M32 - Device Pairing + Trust Handshake Contract

Status: planned/provisional.

Purpose: Define pairing and trust handshake contracts for future devices.

Allowed scope:

- pairing flow contract.
- device identity.
- revocation.
- session scope.
- receipt-backed device events.

Must not add:

- real mobile app.
- push notifications.
- biometrics.
- sensors.
- background services.

Dependencies: M31 native client contract.

Acceptance criteria: device identity, session scope, revocation, and receipt-backed events are specified without a real app or OS integration.

Review prompt required: yes.

Hardening expectation: pairing replay, revocation, and trust downgrade hardening before mobile approval prototype.

Source-of-truth docs: `docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md`, `docs/ui/CCC_NATIVE_CLIENT_STRATEGY.md`.

Notes: Device pairing is not device capability authorization by itself.

## v0.37.0 / M33 - Mobile Approval Surface Prototype, No Sensors

Status: planned/provisional.

Purpose: Prototype mobile approval/status/receipt surfaces without sensors.

Allowed scope:

- approval list API contract.
- receipt viewer contract.
- emergency stop contract.
- web/PWA prototype if explicitly scoped.

Must not add:

- camera.
- microphone.
- GPS.
- contacts.
- calendar.
- photos.
- background services.

Dependencies: M32 pairing/trust handshake contract.

Acceptance criteria: mobile approval and receipt contracts exist without mobile sensor access, native app authority, or background services.

Review prompt required: yes.

Hardening expectation: approval spoofing, receipt clarity, and emergency stop hardening before macOS companion work.

Source-of-truth docs: `docs/canonical/64_mobile_companion_and_device_capability_broker.md`, `docs/ui/CCC_NATIVE_CLIENT_STRATEGY.md`.

Notes: A web/PWA prototype is allowed only if a future prompt explicitly scopes it.

## v0.38.0 / M34 - macOS Local Companion Contract / Prototype

Status: planned/provisional.

Purpose: Plan or prototype a macOS local companion surface.

Allowed scope:

- status/menu-bar planning.
- local runtime status.
- notifications planning.
- receipt/status display.

Must not add:

- keychain access.
- signing/notarization.
- background agent.
- local shell control.
- native build plugin use without approval.

Dependencies: M33 mobile approval surface contracts and CCC macOS planning.

Acceptance criteria: macOS companion role is scoped to status/receipt/approval planning without shell control, keychain, signing, or background agent authority.

Review prompt required: yes.

Hardening expectation: local companion trust and notification policy hardening before Device Capability Broker implementation.

Source-of-truth docs: `docs/ui/CCC_NATIVE_CLIENT_STRATEGY.md`, `docs/canonical/66_external_tooling_and_codex_plugin_governance.md`.

Notes: macOS companion is not a runtime execution path.

## v0.39.0 / M35 - Device Capability Broker Implementation, No Sensors Yet

Status: planned/provisional.

Purpose: Implement Device Capability Broker governance without sensor providers.

Allowed scope:

- capability manifests.
- permission lifecycle.
- risk classification.
- receipt logging.
- revocation.
- no-op/mock providers.

Must not add:

- camera/mic/GPS access.
- background mobile services.
- real OS permission integration.

Dependencies: M34 companion planning and M32 pairing contracts.

Acceptance criteria: Device Capability Broker Implementation, No Sensors Yet creates no-op/mock governance for device capabilities without real sensors or OS permissions.

Review prompt required: yes.

Hardening expectation: broker authorization, revocation, and receipt hardening before selected capture.

Source-of-truth docs: `docs/canonical/64_mobile_companion_and_device_capability_broker.md`, `docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md`.

Notes: M35 is the first Device Capability Broker implementation milestone, but still no sensors.

## v0.40.0 / M36 - Mobile Capture Inbox, Selected Input Only

Status: planned/provisional.

Purpose: Allow user-selected capture input into an inbox for review.

Allowed scope:

- selected text/image/file import contract.
- user-reviewed capture.
- no automatic memory write.

Must not add:

- background scanning.
- contacts/calendar/photos bulk access.
- camera stream.
- mic stream.
- location tracking.

Dependencies: M35 Device Capability Broker implementation and capture policy.

Acceptance criteria: selected capture is user-initiated, inboxed for review, and cannot automatically write memory or scan device data.

Review prompt required: yes.

Hardening expectation: capture provenance, redaction, and deletion hardening before one governed sensor.

Source-of-truth docs: `docs/canonical/64_mobile_companion_and_device_capability_broker.md`, `docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md`.

Notes: Selected capture is not background sensor access.

## v0.41.0 / M37 - One Governed Sensor Capability

Status: planned/provisional.

Purpose: Add exactly one governed sensor capability after the Device Capability Broker is ready.

Allowed scope:

- exactly one capability: camera document scan, or push-to-talk voice clip.
- Device Capability Broker enforcement.
- explicit user gesture.
- no automatic memory write.

Must not add:

- both camera and mic at once.
- always-on mic.
- background location.
- silent photos.
- automatic memory write.
- external send.

Dependencies: M36 selected capture inbox and Device Capability Broker hardening.

Acceptance criteria: exactly one sensor capability is governed by explicit user gesture, broker policy, receipts, and no automatic memory write.

Review prompt required: yes.

Hardening expectation: sensor permission, redaction, and receipt hardening before browser automation contracts.

Source-of-truth docs: `docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md`, `docs/testing/test_strategy_v0.md`.

Notes: Sensor output is not trusted control input by default.

## v0.42.0 / M38 - Browser Automation Contract, No Execution

Status: planned/provisional.

Purpose: Define browser automation contracts without executing browser actions.

Allowed scope:

- browser action envelope.
- browser-use/stagehand/skyvern watchlist.
- policy docs.
- dry-run plan.

Must not add:

- Playwright execution.
- browser profile access.
- logged-in session use.
- real web actions.
- Computer Use.

Dependencies: M37 sensor hardening, approval/sandbox contracts, browser tooling policy.

Acceptance criteria: Browser Automation Contract, No Execution defines dry-run browser action envelopes without real browser automation or profile access.

Review prompt required: yes.

Hardening expectation: browser policy and profile-isolation hardening before any browser-only automation.

Source-of-truth docs: `docs/tooling/CODEX_PLUGIN_RISK_POLICY.md`, `docs/roadmap/ECOSYSTEM_WATCHLIST.md`.

Notes: M38 is no-execution.

## v0.43.0 / M39 - Observability Export Adapters

Status: planned/provisional.

Purpose: Define observability export adapters before higher autonomy.

Allowed scope:

- Langfuse/Phoenix/Opik planned adapters.
- OpenTelemetry export contract.
- local export files.
- redaction and opt-in policies.

Must not add:

- cloud export by default.
- sensitive prompt export.
- secret export.
- production telemetry without opt-in.

Dependencies: M38 browser contract and Event Ledger/redaction policy.

Acceptance criteria: Observability Export Adapters are opt-in, redacted, local-first, and cannot export secrets or sensitive prompts by default.

Review prompt required: yes.

Hardening expectation: telemetry redaction and opt-in hardening before eval/regression harnesses.

Source-of-truth docs: `docs/roadmap/STANDARDS_ALIGNMENT_WATCHLIST.md`, `docs/roadmap/ECOSYSTEM_WATCHLIST.md`.

Notes: Observability is evidence support, not authority.

## v0.44.0 / M40 - Agent Evaluation + Regression Harness

Status: planned/provisional.

Purpose: Add agent eval and regression harnesses before broader autonomy claims.

Allowed scope:

- agent regression suites.
- promptfoo-style evals.
- security evals.
- parity evals.
- memory evals.
- tool-injection evals.

Must not add:

- autonomous execution.
- red-team actions against real systems.
- external API calls without opt-in.

Dependencies: M39 observability export adapters and security test strategy.

Acceptance criteria: Agent Evaluation + Regression Harness covers regressions, security, memory, and tool-injection scenarios without autonomous actions or external API calls by default.

Review prompt required: yes.

Hardening expectation: eval data hygiene, determinism, and false-authority hardening before any autonomy expansion.

Source-of-truth docs: `docs/testing/test_strategy_v0.md`, `docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md`.

Notes: Evals are not proof of production safety by themselves; they are gates and evidence.
## M19 Baseline Note

v0.23.0 / M19 is implemented as Mobile Companion Contract/API Planning only.
M20 Device Capability Broker Contract is implemented/released as contract-only
planning and validation. M21 is implemented/released by v0.25.0 as
contract-only. M22 is implemented/released by v0.26.0 as contract-only and hardened by v0.26.1.
M23-M40 remain planned/provisional. The M19 baseline
adds no mobile app, Android app, iOS app, macOS app, native build workflow, OS
permission integration, mobile sensor access, mobile approval execution,
runtime execution, model/provider calls, remote execution, plugin enablement,
dependency, or production Control Center authority. Capture cannot silently
become memory. Phone/mobile is not the agent brain. Device Capability Broker
contracts are required before sensors.

v0.23.1 is a cleanup/hardening patch for M19 roadmap status and mobile contract
safety tests only. v0.24.0 implements M20 Device Capability Broker Contract
only. v0.25.0 implements M21 OpenWebUI Bridge + Chat Shell Integration
Contract only. M22 Local Model Runtime Activation Contract is implemented by
v0.26.0 as contract/planning/validation only and hardened by v0.26.1. M23-M40 remain
planned/provisional until implemented by dedicated reviewed milestones.
