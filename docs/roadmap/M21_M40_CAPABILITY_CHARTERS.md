# M21-M40 Capability Charters

Status: Active compatibility roadmap projection maintained through v0.59.0. M21-M40 are implemented/released through dedicated reviewed milestones. M34 is implemented/released by v0.38.0 as Broader File Capability Review planning/docs/verifier only. v0.39.0 implements M35 Safe File Review Workflow Contracts as contract-only, review-only logic over already-redacted preview results, v0.39.1 hardens M35 exact file/path binding, v0.40.0 implements M36 CCC File Review Surface, Review-Only as frontend-only, v0.40.1 hardens M36 read-only surface safety, v0.41.0 implements M37 Review Approval Capture, Review-Only Persistence, v0.42.0 implements M38 Safe Context Proposal From Approved Review, v0.43.0 implements M39 CCC Context Proposal Surface, v0.44.0 implements M40 Context Handoff Approval, No Injection, v0.45.0 implements M41 Local Prototype Safety Freeze, v0.46.0 implements M42 Mobile Companion Product Contract Refresh, v0.47.0 implements M43 Mobile API Boundary, Read-Only, v0.48.0 implements M44 CCC iOS Skeleton, No Authority, v0.48.1 hardens the M44 verifier allowance, v0.49.0 implements M45 CCC iOS Local Read-Only Connection, v0.50.0 implements M46 iOS Review/Receipt Read-Only Surfaces, v0.51.0 implements M47 TestFlight Pipeline, Internal Only, v0.52.0 implements M48 First Internal TestFlight Build, v0.53.0 implements M49 Mobile Review Approval Capture, v0.54.0 implements M50 Mobile Approval Audit Hardening, v0.55.0 implements M51 OpenWebUI Bridge Adapter Pilot, v0.56.0 implements M52 OpenWebUI Safe Conversation Surface, v0.57.0 implements M53 Controlled Tool Expansion Review, v0.58.0 implements M54 Safe Media Metadata Inspector, and v0.59.0 implements M55 Redacted Observability Export. M56-M60 remain planned/provisional.

These charters define capability layers after M20. v0.56.0 is the M52 OpenWebUI Safe Conversation Surface baseline after v0.55.0 implemented M51 OpenWebUI Bridge Adapter Pilot. M53 is implemented/released. M54 is implemented/released. M55 is implemented/released and M56-M60 remain future capability layers. Every milestone requires its own implementation prompt, review prompt, hardening expectation, and validation evidence before release.

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

Notes: Free/open-source/self-hosted local runtimes should be evaluated first where practical. M23 is implemented/released by v0.27.0 as separate manual fixed-prompt local call only.

## v0.27.0 / M23 - First Real Local LLM Call, Non-Tool, Non-Authoritative

Status: implemented/released manual-only.

Purpose: Allow the first tightly bounded local LLM inference path.

Allowed scope:

- manual/CLI-only local model call.
- no tools.
- no memory writes.
- no external network.
- no secrets.
- fixed prompt `m23_fixed_local_model_smoke_v1`.
- dry-run by default.
- explicit execute flag.
- local approval validation.
- non-authoritative response.
- receipt summary.

Must not add:

- tool calls.
- autonomous action.
- memory mutation.
- provider/cloud calls.
- freeform OpenWebUI bridge.
- backend API route.
- Control Center execution control.
- arbitrary prompt input.
- user-content model call.

Dependencies: M22 local runtime activation contract and local-only guard.

Acceptance criteria: first local LLM call is manual-only, loopback-only, fixed-prompt-only, approval-gated, non-authoritative, receipt-backed, and cannot mutate state or execute tools. Tests and Foundation Gate use fake transport only.

Review prompt required: yes.

Hardening expectation: v0.27.1 Local LLM Call Hardening is implemented/released and required before memory or tool expansion.

Source-of-truth docs: `docs/runtime/FIRST_LOCAL_LLM_CALL_M23.md`, `docs/runtime/FIRST_LOCAL_LLM_CALL.md`, `docs/runtime/M23_FIXED_PROMPT_POLICY.md`, `docs/runtime/M23_LOCAL_MODEL_CALL_POLICY.md`, `docs/runtime/M23_LOCAL_MODEL_CALL_SAFETY.md`, `docs/runtime/M23_LOCAL_MODEL_CALL_RECEIPTS.md`, `docs/runtime/M23_NON_AUTHORITATIVE_OUTPUT_POLICY.md`, `docs/runtime/M23_MANUAL_CLI_USAGE.md`, `docs/runtime/M23_TO_M24_BOUNDARY.md`, `docs/runtime/LOCAL_RUNTIME_M22_TO_M23_BOUNDARY.md`, `docs/runtime/local_loopback_model_runtime.md`, `docs/runtime/RUNTIME_READINESS.md`, `docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md`.

Notes: Model output remains advisory and must be labeled non-authoritative. v0.27.0 does not add runtime activation, endpoint probes, backend routes, arbitrary prompt input, user-content model calls, tool execution, memory writes, file writes, dependencies, or production authority.

## v0.27.1 - Local LLM Call Hardening

Status: implemented/released hardening-only.

Purpose: Harden the first bounded local LLM path before the next capability jump.

Allowed scope:

- endpoint-label safety checks.
- fixed prompt and CLI guardrails.
- approval validation evidence checks.
- response redaction and caps.
- non-authoritative output checks.
- no secret echo.
- no tool-call leakage.
- Foundation Gate report atomic write/replace safety.

Must not add:

- new tools.
- memory writes.
- cloud providers.
- OpenWebUI freeform bridge.
- autonomous actions.
- backend API routes.
- dependencies.
- runtime behavior expansion.

Dependencies: M23.

Acceptance criteria: local LLM responses are redacted, capped, labeled, timeout-safe, non-authoritative, cannot leak tool-call authority, and cannot be authorized by forged approval-looking data. Foundation Gate latest reports are written through atomic temp-write plus replace so repeated/concurrent-style tooling runs leave valid JSON.

Review prompt required: yes.

Hardening expectation: this is the hardening patch for M23.

Source-of-truth docs: `docs/runtime/FIRST_LOCAL_LLM_CALL.md`, `docs/runtime/FIRST_LOCAL_LLM_CALL_M23.md`, `docs/runtime/M23_FIXED_PROMPT_POLICY.md`, `docs/runtime/M23_LOCAL_MODEL_CALL_POLICY.md`, `docs/runtime/M23_LOCAL_MODEL_CALL_SAFETY.md`, `docs/runtime/M23_LOCAL_MODEL_CALL_RECEIPTS.md`, `docs/runtime/M23_NON_AUTHORITATIVE_OUTPUT_POLICY.md`, `docs/runtime/M23_MANUAL_CLI_USAGE.md`, `docs/runtime/M23_TO_M24_BOUNDARY.md`, `docs/runtime/RUNTIME_READINESS.md`, `docs/testing/test_strategy_v0.md`.

Notes: This patch remains focused on hardening. It adds no runtime behavior, backend route, dependency, memory/tool expansion, or M24 work.

## v0.28.0 / M24 - Memory Provider Abstraction + Local Memory Store

Status: implemented/released.

Purpose: Introduce governed local memory storage carefully.

Allowed scope:

- MemoryProvider abstraction.
- local in-memory/dev memory store.
- explicit-path stdlib SQLite local store.
- memory record lifecycle.
- memory review states.
- user-reviewed writes.
- delete/export contracts.
- source priority, provenance, evidence/event/receipt refs.
- trust/confidence metadata.
- dedup/decay/archive planning metadata.
- recall-planning metadata.

Must not add:

- automatic memory writes.
- unreviewed personal profiling.
- cloud memory providers.
- vector DB.
- embeddings.
- raw session history.
- context injection.
- backend memory mutation API.
- production persistence.

Dependencies: M23 hardening, memory policy, truth/evidence boundaries.

Acceptance criteria: memory writes require review, provenance, delete/export paths, source refs, redacted summary-only storage, no secret storage, no automatic/model/local-LLM/OpenWebUI/mobile/tool writes, no vector DB, no embeddings, no cloud memory, no context injection, no backend mutation route, and OpenAPI path count remains `74`.

Review prompt required: yes.

Hardening expectation: v0.28.1 Memory Safety Hardening before truth/evidence expansion.

Source-of-truth docs: `docs/memory/MEMORY_PROVIDER_ABSTRACTION.md`, `docs/memory/LOCAL_MEMORY_STORE.md`, `docs/memory/MEMORY_RECORD_SCHEMA.md`, `docs/memory/MEMORY_WRITE_POLICY.md`, `docs/memory/MEMORY_SECURITY_MODEL.md`, `docs/memory/M24_TO_M25_BOUNDARY.md`, `docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md`, `src/ultimate_ai_agent/core/memory/`.

Notes: Memory is recall, not authority. Memory is not ground truth. Canonical files, evidence manifests, receipts, Event Ledger records, and user-reviewed sources outrank memory. M25 is implemented/released by v0.29.0 and keeps memory below governed truth sources.

## v0.28.1 - Memory Safety Hardening

Status: implemented/released contract-only.

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

Status: implemented/released contract-only; hardened by v0.29.1 and v0.29.2.

Purpose: Make model claims inspectable.

Allowed scope:

- claim/evidence linking.
- truth-source routing UI.
- evidence refs.
- source summaries.
- claim confidence/review status.
- unknown/arbitrary truth ref denial.

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

## v0.30.0 / M26 - Grounded Recall Router + Evidence-Linked Context Pack Builder

Status: implemented/released contract-only.

Purpose: Define grounded recall and evidence-linked context pack contracts before any context injection.

Allowed scope:

- grounded recall request contracts.
- evidence-linked context pack summaries.
- claim/evidence/source refs.
- redaction and omission metadata.
- context-pack preview manifests.

Must not add:

- raw memory injection.
- raw file injection.
- model/provider calls.
- web search or source fetching.
- automatic context injection.
- memory writes or evidence mutation.

Dependencies: M25 claim/evidence governance and M24 memory boundaries.

Acceptance criteria: grounded recall can describe redacted, evidence-linked context pack plans without injecting context or treating memory as authority.

Review prompt required: yes.

Hardening expectation: context-pack safety hardening before any broader recall or tool-related milestone.

Source-of-truth docs: `docs/recall/GROUNDED_RECALL_ROUTER.md`, `docs/recall/CONTEXT_PACK_BUILDER.md`, `docs/recall/RECALL_SOURCE_PRIORITY.md`, `docs/recall/RECALL_CANDIDATE_POLICY.md`, `docs/recall/CONTEXT_PACK_SAFETY.md`, `docs/recall/RECALL_NON_GOALS.md`, `docs/recall/M26_TO_M27_BOUNDARY.md`, `docs/truth/M25_TO_M26_BOUNDARY.md`, `docs/memory/MEMORY_RECALL_PLANNING.md`, `src/ultimate_ai_agent/core/recall/`.

Notes: M26 is implemented/released by v0.30.0 as local contract logic only and hardened by v0.30.1 for source_ref/source_kind consistency. It adds no runtime context injection, vector search, embeddings, external retrieval, backend route, memory write, model/provider call, tool execution, dependency, or production authority.

## v0.31.0 / M27 - Tool Broker v2 + Safe Tool Intent Contracts

Status: implemented/released contract-only.

Purpose: Define validation-only and preview-only safe tool intent contracts before any real tool execution.

Allowed scope:

- tool target refs.
- tool input boundaries.
- tool catalog entries.
- tool intent decisions.
- non-executing receipt plans.
- static policy checks.
- Foundation Gate coverage.

Must not add:

- real tool execution.
- shell execution.
- file mutation.
- memory writes.
- Event Ledger mutation.
- backend execution routes.
- network calls.
- browser automation.
- plugin enablement.
- model/provider calls.
- context injection.
- production authority.

Dependencies: M26 context-pack boundaries, Approval Authority, Consent Ledger, and existing Tool Broker safety policy.

Acceptance criteria: safe metadata-only tool intents can be previewed while side-effecting, authority-ambiguous, raw, secret-like, model-output, runtime-output, and OpenWebUI-output intents are denied.

Review prompt required: yes.

Hardening expectation: approval/consent binding and sandbox handoff hardening before any execution milestone.

Source-of-truth docs: `docs/tools/TOOL_BROKER_V2.md`, `docs/tools/SAFE_TOOL_INTENT_CONTRACTS.md`, `docs/tools/TOOL_AUTHORITY_BOUNDARY.md`, `docs/tools/TOOL_INTENT_RECEIPT_PLAN.md`, `docs/tools/M27_TO_M28_BOUNDARY.md`, `src/ultimate_ai_agent/core/tools/v2/`.

Notes: Tool Broker v2 decisions are validation decisions, not action approvals and not execution commands.

## v0.32.0 / M28 - Approval Authority v2 + Action Policy Expansion

Status: implemented/released contract-only.

Purpose: Define approval authority and action policy decisions without executing actions.

Allowed scope:

- non-executing approval authority contracts.
- action policy contracts.
- actor/action/resource/scope binding.
- approval grant expiry, revocation, and replay protections.
- approval_ref, approval_test_, and consent_ref denial.
- wildcard approval denial.
- risk and side-effect policy.
- non-authoritative approval receipt plans.
- tests, docs, static verifier coverage, and Foundation Gate coverage.

Must not add:

- action execution.
- tool execution.
- shell/subprocess execution.
- file mutation.
- memory writes.
- network calls.
- model/provider calls.
- browser automation.
- mobile/device access.
- remote execution.
- plugin enablement.
- backend execution routes.
- Control Center execute controls.
- dependencies.
- production authority.

Dependencies: M27 Tool Broker v2 safe intent contracts, M26 context-pack contracts, Consent Ledger, and existing Approval Authority boundaries.

Acceptance criteria: safe no-effect/read-metadata action intents can be allowed for policy with `execution_authorized=False` and `execution_performed=False`, while approval_ref-alone, approval_test_, consent_ref-alone, wildcard, expired, revoked, replayed, mismatched, raw, secret-like, mutating, network, model, browser, mobile, remote, plugin, shell, and destructive actions are denied.

Review prompt required: yes.

Hardening expectation: grant binding, replay resistance, and action policy boundary hardening before any future dry-run or execution milestone.

Source-of-truth docs: `docs/approvals/APPROVAL_AUTHORITY_V2.md`, `docs/approvals/ACTION_POLICY.md`, `docs/approvals/APPROVAL_GRANT_BINDING.md`, `docs/approvals/APPROVAL_EXPIRY_REVOCATION_REPLAY.md`, `docs/approvals/ACTION_RISK_AND_SIDE_EFFECT_POLICY.md`, `docs/approvals/APPROVAL_REF_NOT_AUTHORITY.md`, `docs/approvals/ACTION_POLICY_DECISION_ENVELOPE.md`, `docs/approvals/APPROVAL_RECEIPT_PLAN.md`, `docs/approvals/M28_TO_M29_BOUNDARY.md`, `src/ultimate_ai_agent/core/approvals/v2/`.

Notes: Approval decisions are policy decisions, not action execution.

## v0.32.1 / M28 hardening - Evaluator Revalidation for Raw/Secret Action Inputs

Status: implemented/released hardening-only.

Purpose: Ensure M28 action policy evaluators revalidate current action intent,
approval grant, and action policy state before any policy-only allow decision.

Allowed scope:

- evaluator-side revalidation for raw/secret action inputs.
- `model_copy(update=...)` regression tests.
- Foundation Gate and static verifier probes.
- release notes and archived release packet.

Must not add:

- action execution.
- tool execution.
- backend execution routes.
- file mutation.
- memory writes.
- network, model/provider, browser, mobile, remote, plugin, or shell execution.
- dependencies.
- production authority.
- M29 implementation.

Notes: v0.32.1 preserves safe no-effect/read-metadata policy decisions with
`execution_authorized=False` and `execution_performed=False`.

## v0.33.0 / M29 - Agent Task Planning Engine

Status: implemented/released contract-only.

Purpose: Define deterministic, local, non-executing task planning contracts before any future tool/action execution milestone.

Allowed scope:

- task goal contracts.
- task step contracts.
- task plan contracts.
- dependency graph validation.
- input boundary validation.
- risk and authority policy.
- review-only decision envelopes.
- non-authoritative receipt plans.

Must not add:

- task execution.
- auto-run or scheduler runtime.
- tool execution.
- action execution.
- shell/subprocess execution.
- file mutation.
- memory writes.
- network calls.
- model/provider calls.
- browser/mobile/remote/plugin execution.
- backend task/plan execution routes.
- Control Center execute controls.
- dependencies.
- context injection.
- production authority.
- M30 implementation.

Dependencies: M28 Approval Authority v2 + Action Policy Expansion contracts.

Acceptance criteria: safe task plans can be marked valid for review while raw/secret inputs, non-authoritative refs, risk downgrades, effectful steps, duplicate steps, missing dependencies, and dependency cycles are denied.

Review prompt required: yes.

Hardening expectation: planning boundary and dependency graph hardening before any future dry-run or execution milestone.

Source-of-truth docs: `docs/planning/TASK_PLANNING_ENGINE.md`, `docs/planning/TASK_GOAL_STEP_PLAN_CONTRACTS.md`, `docs/planning/TASK_DEPENDENCY_GRAPH.md`, `docs/planning/TASK_INPUT_BOUNDARY.md`, `docs/planning/TASK_RISK_AND_AUTHORITY_POLICY.md`, `docs/planning/TASK_PLAN_DECISION_ENVELOPE.md`, `docs/planning/TASK_PLAN_RECEIPT_PLAN.md`, `docs/planning/TASK_PLANNING_NON_GOALS.md`, `docs/planning/M29_TO_M30_BOUNDARY.md`, `src/ultimate_ai_agent/core/planning/`.

Notes: M29 plans are non-authoritative and valid for review only.

### v0.33.1 M29 hardening

v0.33.1 hardens Task Plan Dependency, Risk, and No-Execution Safety. It
strengthens duplicate/missing step denial, self/direct/indirect dependency
cycle denial, derived risk enforcement, hidden side-effect denial,
authority-boundary checks, evaluator revalidation, static verifier coverage,
and Foundation Gate coverage. It adds no task execution, scheduler/background
worker, action execution, tool execution, backend execution route, dependency,
M30 implementation, or production authority.

## v0.34.0 / M30 - Multi-Step Execution Framework

Status: implemented/released contract-only.

Purpose: Define deterministic, local, side-effect-safe execution-state-machine contracts before any future real execution milestone.

Allowed scope:

- execution run contracts.
- execution step contracts.
- transition request and decision contracts.
- dependency-aware no-effect progression.
- replay protection.
- evaluator-side revalidation.
- non-authoritative receipt plans.
- static verifier and Foundation Gate coverage.

Must not add:

- real task execution.
- action execution.
- tool execution.
- scheduler/background worker or autonomous loop.
- shell execution.
- file mutation.
- memory writes or Event Ledger mutation.
- network calls.
- model/provider calls.
- browser/mobile/plugin actions.
- remote execution.
- backend execution routes.
- Control Center execute controls.
- dependencies.
- context injection.
- production authority.
- M31 implementation.

Dependencies: M29 Agent Task Planning Engine no-execution hardening.

Acceptance criteria: safe no-effect transitions can advance deterministic state while replay, dependency, raw/secret, authority, scheduler/background, and execution probes are denied with stable reason codes and `execution_performed=False`.

Review prompt required: yes.

Hardening expectation: state-machine safety hardening before any future execution-expansion milestone.

Source-of-truth docs: `docs/execution/MULTI_STEP_EXECUTION_FRAMEWORK.md`, `docs/execution/EXECUTION_STATE_MACHINE.md`, `docs/execution/EXECUTION_STEP_CONTRACTS.md`, `docs/execution/EXECUTION_DEPENDENCY_POLICY.md`, `docs/execution/EXECUTION_TRANSITION_POLICY.md`, `docs/execution/EXECUTION_INPUT_BOUNDARY.md`, `docs/execution/EXECUTION_RECEIPT_PLAN.md`, `docs/execution/EXECUTION_NON_GOALS.md`, `docs/execution/M30_TO_M31_BOUNDARY.md`, `src/ultimate_ai_agent/core/execution/`.

Notes: M30 transition decisions are non-authoritative and state-machine only.

v0.34.1 hardens Execution State Machine, Replay, and No-Side-Effect Safety. It
strengthens ready-only step completion, invalid transition denial, incomplete
finalize denial, replay-key and transition-id denial, hidden side-effect
metadata denial, evaluator revalidation, static verifier coverage, and
Foundation Gate coverage. It adds no task execution, scheduler/background
worker, action execution, tool execution, backend execution route, dependency,
M31 implementation, or production authority.

## v0.35.0 / M31 - Real Tool Runtime Adapter, Single Safe No-Op Tool

Status: implemented/released.

Purpose: Add the first governed local tool runtime adapter while allowing only one deterministic safe no-op tool.

Allowed scope:

- real runtime adapter contracts for `tool:no_op.v1`.
- deterministic no-op invocation only.
- no-op input, output, decision, and receipt-plan contracts.
- replay-key protection.
- evaluator revalidation for pre-built and model_copy-mutated requests.
- static verifier and Foundation Gate coverage.

Must not add:

- arbitrary or effectful tool execution.
- dynamic dispatch, module loading, callable lookup, plugin enablement, or shell/subprocess execution.
- file mutation, memory writes, Event Ledger mutation, network calls, model/provider calls, browser/mobile/remote/plugin actions, scheduler/background worker, backend execute routes, Control Center execute controls, dependencies, M32 work, or production authority.

## v0.35.1 / M31 hardening - No-Op Tool Runtime Adapter Safety

Status: implemented/released.

Purpose: Harden the no-op-only runtime adapter so caller-mutated request objects
and metadata cannot smuggle dynamic dispatch or side-effect requests past
constructor validation.

Hardening scope:

- tool allowlist and tool_ref/tool_name consistency checks.
- dynamic dispatch denial for hidden module/callable/function fields.
- side-effect denial for hidden or metadata-backed file, memory, network, model,
  shell, browser, mobile, remote, plugin, environment, and secret lookup fields.
- authority-boundary checks for approvals, plans, context packs, memory, model,
  runtime, OpenWebUI, and arbitrary refs.
- evaluator revalidation for pre-built and model_copy-mutated requests.
- static verifier and Foundation Gate probes for the bypass.

Must not add:

- arbitrary or effectful tool execution.
- shell/subprocess execution, file mutation, memory writes, Event Ledger
  mutation, network calls, model/provider calls, browser/mobile/remote/plugin
  actions, scheduler/background worker, backend execute routes, Control Center
  execute controls, dependencies, M32 work, or production authority.

Dependencies: M27 Tool Broker v2 contracts, M28 Approval Authority v2, M29 review-only planning, and M30 state-machine-only execution contracts.

Acceptance criteria: only `tool:no_op.v1` can be invoked; no-op completion is deterministic and records `side_effects_performed=[]`; raw input is not echoed or stored; approval refs, `approval_test_*`, task plans, tool intents, context packs, memory, model/runtime/OpenWebUI output, and Control Center refs cannot authorize invocation; OpenAPI path count remains `74`; M32-M40 remain planned/provisional.

Review prompt required: yes.

Hardening expectation: no-op runtime safety hardening before any broader safe tool runtime expansion.

Source-of-truth docs: `docs/tools/TOOL_RUNTIME_ADAPTER.md`, `docs/tools/NOOP_TOOL_RUNTIME.md`, `docs/tools/TOOL_RUNTIME_INVOCATION_CONTRACT.md`, `docs/tools/TOOL_RUNTIME_AUTHORITY_BOUNDARY.md`, `docs/tools/TOOL_RUNTIME_REPLAY_POLICY.md`, `docs/tools/TOOL_RUNTIME_RECEIPT_PLAN.md`, `docs/tools/TOOL_RUNTIME_NON_GOALS.md`, `docs/tools/M31_TO_M32_BOUNDARY.md`, `src/ultimate_ai_agent/core/tools/runtime/`.

Notes: M31 is real runtime plumbing for a no-op tool only. It is not arbitrary tool execution.

## v0.36.0 / M32 - Safe Local Filesystem Metadata Tool

Status: implemented/released.

Purpose: Add exactly one safe local filesystem metadata tool through the governed Tool Runtime Adapter.

Allowed scope:

- `tool:filesystem_metadata.v1`.
- server-owned safe roots.
- relative path metadata lookup.
- safe refs, existence, kind, size, extension, and modified-time metadata.
- metadata-only receipt planning.
- stricter path, authority, content, symlink, and mutation denial.

Must not add:

- arbitrary tool execution.
- shell/subprocess execution.
- file content reads.
- text previews or content hashes.
- directory listing or recursive traversal.
- symlink following.
- caller-selected arbitrary roots.
- file mutation.
- memory, network, model, browser, mobile, remote, or plugin actions.
- backend execute routes.
- production authority.

Dependencies: M31 no-op runtime adapter.

Acceptance criteria: safe metadata lookup succeeds under a server-owned safe root; unsafe paths, symlinks, caller roots, raw content, previews, hashes, listings, recursion, mutation, and authority-ref bypasses are denied; OpenAPI path count remains `74`.

Review prompt required: yes.

Hardening expectation: path policy, safe-root registry, result envelope, and static verifier hardening before any broader filesystem capability.

Source-of-truth docs: `docs/tools/FILESYSTEM_METADATA_TOOL.md`, `docs/tools/FILESYSTEM_METADATA_PATH_POLICY.md`, `docs/tools/FILESYSTEM_METADATA_RESULT_CONTRACT.md`, `docs/tools/FILESYSTEM_METADATA_AUTHORITY_BOUNDARY.md`, `docs/tools/FILESYSTEM_METADATA_NON_GOALS.md`, `docs/tools/M32_TO_M33_BOUNDARY.md`, `src/ultimate_ai_agent/core/tools/runtime/filesystem_metadata.py`.

Notes: Device, native-client, and pairing work remains future roadmap material and is not implemented by M32.

## v0.36.1 / M32 hardening - Filesystem Metadata Path Safety

Status: implemented/released hardening-only.

Purpose: Harden M32 filesystem metadata path safety before any broader
filesystem or mobile approval milestone.

Allowed scope:

- encoded traversal denial.
- home-directory, Windows drive, doubled-separator, and unsafe-separator denial.
- hidden and private-key-like path denial.
- caller-selected root denial.
- metadata alias flag denial.
- model_copy evaluator revalidation.
- static verifier, documentation, and Foundation Gate coverage.

Must not add:

- raw file content reads.
- text previews or content hashes.
- directory listing or recursive traversal.
- symlink following.
- arbitrary tool execution.
- shell/subprocess execution.
- file mutation.
- memory, network, model, browser, mobile, remote, or plugin actions.
- backend execute or raw-file routes.
- Control Center execute or raw-preview controls.
- dependencies.
- M33 work.

Acceptance criteria: unsafe path encodings, private-key-like paths,
caller-selected roots, unsafe metadata alias flags, and model_copy-mutated
metadata/tool_ref bypasses are denied; valid metadata-only safe-root lookup
still succeeds; OpenAPI path count remains `74`.

Review prompt required: yes.

Hardening expectation: this is the M32 path-safety hardening patch.

## v0.37.0 / M33 - First Safe Local File Read Proposal, Redacted Preview Only

Status: implemented/released.

Purpose: Add exactly one bounded redacted file preview proposal tool through the governed Tool Runtime Adapter.

Allowed scope:

- `tool:filesystem.redacted_preview.v1`.
- server-owned safe roots or explicit test fixtures.
- relative path preview requests.
- small UTF-8 text preview bytes read only inside the redaction pipeline.
- redaction-before-return.
- redacted preview result contract.
- redaction summary.
- no-raw-content receipt planning.
- static verifier and Foundation Gate coverage.

Must not add:

- raw file content output or storage.
- full-file read output.
- unredacted file preview.
- content hash.
- directory listing or recursive traversal.
- symlink following.
- caller-selected arbitrary roots.
- hidden or secret-like path reads.
- file writes, deletes, chmod, chown, rename, copy, move, or mutation.
- arbitrary filesystem tools.
- shell/subprocess execution.
- memory writes.
- network, model, browser, mobile, remote, or plugin actions.
- context injection.
- backend raw-file or execute routes.
- Control Center raw-preview or execute controls.
- dependencies or production authority.

Dependencies: M31 no-op runtime adapter and M32 filesystem metadata path policy.

Acceptance criteria: safe redacted preview succeeds under a server-owned safe
root; raw/full/hash/listing/mutation flags, unsafe paths, symlinks, directories,
binary files, unsupported encodings, oversized files, caller roots, and
authority-ref bypasses are denied; redacted results return no raw content or raw
absolute path; OpenAPI path count remains `74`.

Review prompt required: yes.

Hardening expectation: redaction policy, safe-root registry, result envelope, and
static verifier hardening before any broader filesystem capability.

Source-of-truth docs: `docs/tools/REDACTED_FILE_PREVIEW_TOOL.md`, `docs/tools/REDACTED_FILE_PREVIEW_POLICY.md`, `docs/tools/REDACTED_FILE_PREVIEW_RESULT_CONTRACT.md`, `docs/tools/REDACTED_FILE_PREVIEW_REDACTION_POLICY.md`, `docs/tools/REDACTED_FILE_PREVIEW_AUTHORITY_BOUNDARY.md`, `docs/tools/REDACTED_FILE_PREVIEW_NON_GOALS.md`, `docs/tools/M33_TO_M34_BOUNDARY.md`, `src/ultimate_ai_agent/core/tools/runtime/file_preview.py`.

Notes: M33 is redacted preview only. M34 is implemented/released by v0.38.0 as
broader file capability review planning/docs/verifier only.

### v0.37.1 / M33 hardening - Redacted File Preview Safety

Status: implemented/released.

Purpose: Harden M33 redacted preview safety without expanding file capability.

Acceptance criteria: symlink safe roots are denied before preview; secret-like
preview text is rejected at the output contract boundary; evaluator boundaries
revalidate safety-critical fields; static verifier and Foundation Gate probe the
same bypasses; OpenAPI path count remains `74`.

Hardening expectation: this is the M33 redacted preview safety hardening patch.
M34 is implemented/released by v0.38.0 as broader file capability review
planning/docs/verifier only.

### v0.37.2 / Local Developer Launcher + Desktop Shortcut

Status: implemented/released tooling-only.

Purpose: Add local developer launcher tooling for prototype testing without
starting M34 or adding agent capability.

Acceptance criteria: `./scripts/dev/uaa` supports doctor, start, ui, status,
logs, stop, and restart; the launcher binds only to localhost; PID/log files
live under ignored `.uaa/dev/`; a macOS `.command` launcher generator can open
the local Control Center; no backend routes, tool/action execution,
model/provider calls, dependencies, production installer, M34 work, or
production authority are added.

Source-of-truth docs: `docs/developer/LOCAL_LAUNCHER.md`,
`scripts/dev/README.md`.

### v0.37.3 / Roadmap Label Alignment + Documentation Integrity Guard

Status: implemented/released docs/verifier-only.

Purpose: Align active roadmap/currentness docs on the planned v0.38.0 / M34
label and add documentation-integrity coverage so active docs cannot disagree
about the next planned milestone label.

Acceptance criteria: active roadmap/current docs consistently use
`v0.38.0 / M34 - Broader File Capability Review`; stale M34 labels are rejected
by documentation integrity verification; no M34 implementation, route,
dependency, runtime behavior, or production authority is added.

Source-of-truth docs: `docs/release_notes/v0_37_3.md`,
`docs/archive/releases/v0_37_3/README_IMPORT.md`,
`docs/archive/releases/v0_37_3/master_plan.md`.

### v0.37.4 / Roadmap Supersession Through M60 + Documentation Integrity Guard

Status: implemented/released docs/verifier-only.

Purpose: Supersede the old active post-M33 projection and define the active
M34-M60 sequence without starting M34 implementation.

Acceptance criteria: active roadmap/current docs consistently use the M34-M60
sequence from `docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md`; M34 is
planning/docs/verifier only; M35 is the first implementation after
supersession; M42 resumes mobile planning; M44 is the first iOS skeleton; M47
is the TestFlight-capable pipeline; M48 is the first internal TestFlight build;
M49-M50 are mobile review approval capture and audit work; no M34
implementation, route, dependency, runtime behavior, mobile/TestFlight
implementation, or production authority is added.

Source-of-truth docs: `docs/release_notes/v0_37_4.md`,
`docs/archive/releases/v0_37_4/README_IMPORT.md`,
`docs/archive/releases/v0_37_4/master_plan.md`,
`docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md`.

## v0.38.0 / M34 - Broader File Capability Review

Status: implemented/released planning/docs/verifier only.

Purpose: Plan the broader file review/capability boundary after M33 redacted
preview without granting raw file access, context injection, mutation, or
execution authority.

Allowed scope:

- broader file capability review.
- safe file review planning.
- redacted review and approval-boundary planning.
- no-authority file workflow contracts.
- file capability boundary matrix.
- file capability risk register.
- file capability decision record.
- M35 Safe File Review Workflow readiness guidance.
- documentation-integrity checks, static verification, and Foundation Gate coverage.

Must not add:

- raw file output or storage.
- context injection.
- memory writes.
- file writes/deletes/mutation.
- backend raw-file/review-approval/execute routes.
- Control Center raw-preview/execute controls.
- Safe File Review Workflow implementation.
- File Review Control Center Surface.
- Review Approval Capture.
- context proposal or context injection.
- memory writes.
- export.
- execution.
- production authority.

Dependencies: M33 redacted file preview proposal and active file/tool authority
boundaries.

Acceptance criteria: v0.38.0 marks M34 implemented/released as planning,
architecture review, documentation, verifier, and Foundation Gate work only. It
adds no runtime file capability, backend route, frontend runtime feature, raw
file read, file review workflow implementation, approval capture, context
proposal, context injection, memory write, export, execution, dependency, or
production authority. v0.39.0 implements M35 as contract-only Safe File Review
Workflow Contracts, v0.39.1 hardens exact file/path binding, and v0.40.0
implements M36 as CCC File Review Surface, Review-Only; v0.40.1 hardens M36 read-only surface safety; v0.41.0
implements M37 as Review Approval Capture, Review-Only Persistence; v0.42.0
implements M38 as Safe Context Proposal From Approved Review; M39 is
implemented/released by v0.43.0 as CCC Context Proposal Surface; M40 is
implemented/released by v0.44.0 as Context Handoff Approval, No Injection; M41 is
implemented/released by v0.45.0 as Local Prototype Safety Freeze; M42-M60 remain
planned/provisional.

Review prompt required: yes.

Hardening expectation: M35 must carry file review packet no-authority
guarantees, redaction verification, raw-content denial, and
context-injection/memory-write/export/execution denial before any broader file
capability is accepted.

Source-of-truth docs: `docs/canonical/09_roadmap.md`,
`docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md`,
`docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md`,
`docs/files/BROADER_FILE_CAPABILITY_REVIEW.md`,
`docs/files/FILE_CAPABILITY_BOUNDARY_MATRIX.md`,
`docs/files/FILE_CAPABILITY_RISK_REGISTER.md`,
`docs/files/FILE_CAPABILITY_DECISION_RECORD.md`,
`docs/files/M35_SAFE_FILE_REVIEW_WORKFLOW_READINESS.md`,
`docs/files/M34_TO_M35_BOUNDARY.md`,
`docs/tools/M33_TO_M34_BOUNDARY.md`.

Notes: macOS companion is not a runtime execution path.

## v0.39.0 / M35 - Safe File Review Workflow Contracts

Status: implemented/released contract-only.

Purpose: Add the first implementation after the v0.37.4 supersession: safe file
review workflow contracts that preserve redacted-only review and no-authority
approval boundaries.

Allowed scope:

- review packet contracts over redacted previews.
- redaction verification contracts.
- exact review packet binding plans.
- no-authority decision and receipt plans.

Must not add:

- raw file output or storage.
- full-file reads.
- context injection.
- memory writes.
- export.
- execution.
- backend raw-file/review-approval/execute routes.

Review prompt required: yes.

Hardening expectation: mandatory M35 hardening for exact packet binding,
redaction verification, approval_ref denial, and evaluator revalidation.

Source-of-truth docs: `docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md`,
`docs/files/SAFE_FILE_REVIEW_WORKFLOW.md`,
`docs/files/FILE_REVIEW_PACKET_CONTRACT.md`,
`docs/files/FILE_REVIEW_USER_APPROVAL_GATE.md`,
`docs/files/FILE_REVIEW_AUTHORITY_BOUNDARY.md`,
`docs/files/FILE_REVIEW_RECEIPT_PLAN.md`,
`docs/files/FILE_REVIEW_NON_GOALS.md`, and
`docs/files/M35_TO_M36_BOUNDARY.md`.

## v0.39.1 / M35 hardening - File Review Exact File/Path Binding

Status: implemented/released hardening.

Purpose: Repair and harden M35 so review approvals bind to the exact actor,
review packet, preview result, redaction summary, file_ref, and safe_path_ref.

Allowed scope:

- exact file_ref binding.
- exact safe_path_ref binding.
- model_copy-mutated file/path denial at evaluator boundaries.
- tests, docs, static verification, documentation-integrity checks, and
  Foundation Gate coverage.

Must not add:

- Control Center file review UI.
- approval capture or persistence.
- context proposal or context injection.
- raw file access, full-file reads, export, execution, backend routes, or
  dependencies.

Review prompt required: yes.

Hardening expectation: complete for the v0.39.1 repair baseline; future M35
hardening must remain patch-only and avoid M36 implementation.

Source-of-truth docs: `docs/files/SAFE_FILE_REVIEW_WORKFLOW.md`,
`docs/files/FILE_REVIEW_USER_APPROVAL_GATE.md`, and
`docs/files/M35_TO_M36_BOUNDARY.md`.

## v0.40.0 / M36 - CCC File Review Surface, Review-Only

Status: implemented/released frontend-only.

Purpose: Add a read-only/review-only CCC file review surface after M35
contracts exist.

Allowed scope:

- redacted review packet display.
- review-only status and receipt summaries.
- local browser smoke review.

Must not add:

- raw-preview controls.
- execute controls.
- approval mutation authority.
- context injection.
- memory writes.
- backend route drift.

Review prompt required: yes.

Hardening expectation: mandatory M36 hardening for browser-smoke reviewability,
redacted display, and no execute/raw-preview controls.

Source-of-truth docs: `docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md`.
M37 is implemented/released. M38 is implemented/released by v0.42.0. M39
remains planned/provisional.

## v0.41.0 / M37 - Review Approval Capture, Review-Only Persistence

Status: implemented/released.

Purpose: Capture review approvals with audit-only persistence while preserving
review-only and non-authoritative boundaries.

Allowed scope:

- review approval capture contracts.
- review-only persistence/audit metadata.
- exact packet binding and revocation/replay plans.

Must not add:

- raw access authority.
- context injection authority.
- memory write authority.
- export or execution authority.

Review prompt required: yes.

Hardening expectation: extra-hard review and mandatory hardening for approval
binding, replay, revocation, and no-authority guarantees.

Source-of-truth docs: `docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md`.

## v0.42.0 / M38 - Safe Context Proposal From Approved Review

Status: implemented/released frontend-only.

Purpose: Create safe context proposal contracts from approved review packets
without automatic context injection.

Allowed scope:

- context proposal contracts.
- redacted summary and source-ref plans.
- proposal decision envelopes.

Must not add:

- automatic context injection.
- prompt/provider payload exposure.
- model authority.
- memory writes.
- execution.

Review prompt required: yes.

Hardening expectation: extra-hard review and mandatory hardening for proposal
authority boundaries and no-injection guarantees.

Source-of-truth docs: `docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md`.

## v0.43.0 / M39 - CCC Context Proposal Surface

Status: implemented/released contract-only.

Purpose: Add a review-only CCC surface for context proposals after M38
contracts exist.

Allowed scope:

- proposal summary display.
- source-ref and receipt summary display.
- browser smoke review.

Must not add:

- prompt injection controls.
- model/provider calls.
- memory writes.
- execute controls.

Review prompt required: yes.

Hardening expectation: mandatory M39 hardening for browser-smoke reviewability
and no-injection UI boundaries.

Source-of-truth docs: `docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md`.

## v0.44.0 / M40 - Context Handoff Approval, No Injection

Status: planned/provisional.

Purpose: Add an approval boundary for context handoff decisions without
automatic context injection.

Allowed scope:

- handoff approval contracts.
- exact proposal binding.
- no-injection decision envelopes.

Must not add:

- automatic context injection.
- provider/model authority.
- execution.
- unreviewed memory writes.

Review prompt required: yes.

Hardening expectation: extra-hard review and mandatory hardening for proposal
binding, approval refs, and no-injection guarantees.

Source-of-truth docs: `docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md`.

## M42-M60 Active Supersession Pointer

v0.45.0 / M41 - Local Prototype Safety Freeze is implemented/released safety freeze.
v0.46.0 / M42 - Mobile Companion Product Contract Refresh is implemented/released contract refresh.
v0.47.0 / M43 - Mobile API Boundary, Read-Only is implemented/released contract-only.
v0.48.0 / M44 - CCC iOS Skeleton, No Authority is implemented/released source-only.
v0.49.0 / M45 - CCC iOS Local Read-Only Connection is implemented/released contract/status-only.
v0.50.0 / M46 - iOS Review/Receipt Read-Only Surfaces is implemented/released source-only read-only.
v0.51.0 / M47 - TestFlight Pipeline, Internal Only is implemented/released contract/checklist-only.
M41 is implemented/released by v0.45.0 as Local Prototype Safety Freeze. M42 is implemented/released by v0.46.0 as Mobile Companion Product Contract Refresh. M43 is implemented/released by v0.47.0 as Mobile API Boundary, Read-Only. M44 is implemented/released by v0.48.0 as CCC iOS Skeleton, No Authority. v0.48.1 hardens the M44 verifier allowance. M45 is implemented/released by v0.49.0 as CCC iOS Local Read-Only Connection. M46 is implemented/released by v0.50.0 as iOS Review/Receipt Read-Only Surfaces. M47 is implemented/released by v0.51.0 as TestFlight Pipeline, Internal Only. M48 is implemented/released by v0.52.0 as First Internal TestFlight Build. M49 is implemented/released by v0.53.0 as Mobile Review Approval Capture. M50 is implemented/released by v0.54.0 as Mobile Approval Audit Hardening. M51 is implemented/released by v0.55.0 as OpenWebUI Bridge Adapter Pilot. M52 is implemented/released by v0.56.0 as OpenWebUI Safe Conversation Surface. M53 is implemented/released. M54 is implemented/released. M55 is implemented/released and M56-M60 are planned/provisional in
`docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md`. This compatibility document
keeps the M21-M40 filename for existing verifier and documentation links, but
the active post-M33 sequence through M60 is defined by the supersession page.
## M19 Baseline Note

v0.23.0 / M19 is implemented as Mobile Companion Contract/API Planning only.
M20 Device Capability Broker Contract is implemented/released as contract-only
planning and validation. M21 is implemented/released by v0.25.0 as
contract-only. M22 is implemented/released by v0.26.0 as contract-only and hardened by v0.26.1.
M23 is implemented/released by v0.27.0 as manual fixed-prompt local call only.
M24 is implemented/released by v0.28.0 as governed local memory provider/store foundation, hardened by v0.28.1, and docs-cleaned by v0.28.2.
M25 is implemented/released by v0.29.0 as deterministic local truth/evidence contracts. M26 is implemented/released by v0.30.0 as deterministic local grounded recall/context-pack contracts and hardened by v0.30.1. M27 is implemented/released by v0.31.0 as validation-only Tool Broker v2 contracts. v0.31.1 is docs-only README polish baseline normalization. M28 is implemented/released by v0.32.0 as Approval Authority v2 + Action Policy Expansion. M29 is implemented/released by v0.33.0 as Agent Task Planning Engine and hardened by v0.33.1 for dependency graph, derived risk, hidden side-effect, authority-boundary, evaluator revalidation, and no-execution coverage. M30 is implemented/released by v0.34.0 as Multi-Step Execution Framework state-machine-only contracts and hardened by v0.34.1. M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool. M32 is implemented/released by v0.36.0 and hardened by v0.36.1. M33 is implemented/released by v0.37.0 as First Safe Local File Read Proposal, Redacted Preview Only and hardened by v0.37.1 for redacted preview safety. M34 is implemented/released by v0.38.0 as Broader File Capability Review planning/docs/verifier only. M35 is implemented/released by v0.39.0 as Safe File Review Workflow Contracts and hardened by v0.39.1 for exact file/path binding. M36 is implemented/released by v0.40.0 as CCC File Review Surface, Review-Only. M37 is implemented/released by v0.41.0 as Review Approval Capture, Review-Only Persistence. M38 is implemented/released by v0.42.0 as Safe Context Proposal From Approved Review. M39 is implemented/released by v0.43.0 as CCC Context Proposal Surface. M40 is implemented/released by v0.44.0 as Context Handoff Approval, No Injection. M41 is implemented/released by v0.45.0 as Local Prototype Safety Freeze. M42 is implemented/released by v0.46.0 as Mobile Companion Product Contract Refresh. M43 is implemented/released by v0.47.0 as Mobile API Boundary, Read-Only. M44 is implemented/released by v0.48.0 as CCC iOS Skeleton, No Authority. v0.48.1 hardens the M44 verifier allowance. M45 is implemented/released by v0.49.0 as CCC iOS Local Read-Only Connection. M46 is implemented/released by v0.50.0 as iOS Review/Receipt Read-Only Surfaces. M47 is implemented/released by v0.51.0 as TestFlight Pipeline, Internal Only. M48 is implemented/released by v0.52.0 as First Internal TestFlight Build. M49 is implemented/released by v0.53.0 as Mobile Review Approval Capture. M50 is implemented/released by v0.54.0 as Mobile Approval Audit Hardening. M51 is implemented/released by v0.55.0 as OpenWebUI Bridge Adapter Pilot. M52 is implemented/released by v0.56.0 as OpenWebUI Safe Conversation Surface. M53 is implemented/released. M54 is implemented/released. M55 is implemented/released and M56-M60 remain planned/provisional. The M19 baseline
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
v0.26.0 as contract/planning/validation only and hardened by v0.26.1. M23 is
implemented/released by v0.27.0 as manual fixed-prompt local call only. M24 is
implemented/released by v0.28.0 as governed local memory provider/store foundation, hardened by v0.28.1, and docs-cleaned by v0.28.2. M25 is implemented/released by v0.29.0 as deterministic local truth/evidence contracts. M26 is implemented/released by v0.30.0 as deterministic local grounded recall/context-pack contracts and hardened by v0.30.1. M27 is implemented/released by v0.31.0 as validation-only Tool Broker v2 contracts. M28 is implemented/released by v0.32.0 as Approval Authority v2 + Action Policy Expansion. M29 is implemented/released by v0.33.0 as Agent Task Planning Engine and hardened by v0.33.1. M30 is implemented/released by v0.34.0 as Multi-Step Execution Framework and hardened by v0.34.1. M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool. M32 is implemented/released by v0.36.0 and hardened by v0.36.1. M33 is implemented/released by v0.37.0 as First Safe Local File Read Proposal, Redacted Preview Only and hardened by v0.37.1 for redacted preview safety. M36 is implemented/released by v0.40.0 as CCC File Review Surface, Review-Only. M37 is implemented/released by v0.41.0. M38 is implemented/released by v0.42.0. M39 is implemented/released by v0.43.0. M40 is implemented/released by v0.44.0. M41 is implemented/released by v0.45.0. M42-M60
remain planned/provisional until implemented by dedicated reviewed milestones.
