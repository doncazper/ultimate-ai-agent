# M21-M40 Capability Charters

Status: Active roadmap projection maintained through v0.37.1. M21 and M22 are implemented/released contract-only; M23 is implemented/released manual fixed-prompt local call only and hardened by v0.27.1; M24 is implemented/released as governed memory provider/local store, hardened by v0.28.1, and docs-cleaned by v0.28.2; M25 is implemented/released contract-only and hardened by v0.29.1 and v0.29.2; M26 is implemented/released as deterministic grounded recall/context-pack contracts and hardened by v0.30.1; M27 is implemented/released as validation-only Tool Broker v2 contracts; v0.31.1 is docs-only baseline normalization; M28 is implemented/released as Approval Authority v2 + Action Policy Expansion and hardened by v0.32.1; M29 is implemented/released as Agent Task Planning Engine; M30 is implemented/released as Multi-Step Execution Framework state-machine-only contracts and hardened by v0.34.1; M31 is implemented/released as Real Tool Runtime Adapter, Single Safe No-Op Tool and hardened by v0.35.1 for no-op runtime adapter safety; M32 is implemented/released as Safe Local Filesystem Metadata Tool and hardened by v0.36.1; M33 is implemented/released as First Safe Local File Read Proposal, Redacted Preview Only and hardened by v0.37.1; M34-M40 remain planned/provisional.

These charters define capability layers after M20. v0.25.0 implements M21 as contract/planning/validation only. v0.26.0 implements M22 as contract/planning/validation only, and v0.26.1 hardens M22 verifier precision plus metadata key secret hygiene only. v0.27.0 implements M23 as manual/CLI-only, loopback-only, fixed-prompt-only, non-tool, and non-authoritative. v0.27.1 hardens M23 local call safety without adding new runtime authority. v0.28.0 implements M24 as governed, reviewed-write-only local memory provider/store foundation, v0.28.1 repairs/hardens the M24 memory contract without adding new authority, and v0.28.2 removes a duplicate roadmap row only. v0.29.0 implements M25 as deterministic local truth/evidence contracts over provided refs only, v0.29.1 hardens unknown/arbitrary truth ref denial, and v0.29.2 hardens local-dev API authority/raw preview safety. v0.30.0 implements M26 as deterministic local grounded recall/context-pack contracts, v0.30.1 hardens source_ref/source_kind consistency, v0.31.0 implements M27 Tool Broker v2 + Safe Tool Intent Contracts as validation-only and preview-only contract logic, v0.31.1 normalizes the GitHub README polish commit into a clean docs-only baseline, v0.32.0 implements M28 Approval Authority v2 + Action Policy Expansion as policy-only contracts, v0.32.1 hardens evaluator revalidation for raw/secret action inputs, v0.33.0 implements M29 Agent Task Planning Engine as deterministic, local, non-executing, review-only planning contracts, v0.34.0 implements M30 Multi-Step Execution Framework as deterministic, local, side-effect-safe, state-machine-only contracts, v0.34.1 hardens M30 state transitions, replay protection, dependency gating, hidden side-effect denial, evaluator revalidation, and no-side-effect invariants, v0.35.0 implements M31 Real Tool Runtime Adapter, Single Safe No-Op Tool as a governed no-op-only runtime adapter, v0.35.1 hardens M31 no-op runtime adapter safety, v0.36.0 implements M32 Safe Local Filesystem Metadata Tool, v0.36.1 hardens M32 filesystem metadata path safety, v0.37.0 implements M33 First Safe Local File Read Proposal, Redacted Preview Only, and v0.37.1 hardens M33 redacted file preview safety. M34-M40 remain future capability layers. Every milestone requires its own implementation prompt, review prompt, hardening expectation, and validation evidence before release.

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

Notes: M33 is redacted preview only. M34 remains future broader file capability work.

### v0.37.1 / M33 hardening - Redacted File Preview Safety

Status: implemented/released.

Purpose: Harden M33 redacted preview safety without expanding file capability.

Acceptance criteria: symlink safe roots are denied before preview; secret-like
preview text is rejected at the output contract boundary; evaluator boundaries
revalidate safety-critical fields; static verifier and Foundation Gate probe the
same bypasses; OpenAPI path count remains `74`.

Hardening expectation: this is the M33 redacted preview safety hardening patch.
M34 remains future broader file capability work.

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

Dependencies: future reviewed companion planning and trust-boundary contracts.

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
M23 is implemented/released by v0.27.0 as manual fixed-prompt local call only.
M24 is implemented/released by v0.28.0 as governed local memory provider/store foundation, hardened by v0.28.1, and docs-cleaned by v0.28.2.
M25 is implemented/released by v0.29.0 as deterministic local truth/evidence contracts. M26 is implemented/released by v0.30.0 as deterministic local grounded recall/context-pack contracts and hardened by v0.30.1. M27 is implemented/released by v0.31.0 as validation-only Tool Broker v2 contracts. v0.31.1 is docs-only README polish baseline normalization. M28 is implemented/released by v0.32.0 as Approval Authority v2 + Action Policy Expansion. M29 is implemented/released by v0.33.0 as Agent Task Planning Engine and hardened by v0.33.1 for dependency graph, derived risk, hidden side-effect, authority-boundary, evaluator revalidation, and no-execution coverage. M30 is implemented/released by v0.34.0 as Multi-Step Execution Framework state-machine-only contracts and hardened by v0.34.1. M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool. M32 is implemented/released by v0.36.0 and hardened by v0.36.1. M33 is implemented/released by v0.37.0 as First Safe Local File Read Proposal, Redacted Preview Only and hardened by v0.37.1 for redacted preview safety. M34-M40 remain planned/provisional. The M19 baseline
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
implemented/released by v0.28.0 as governed local memory provider/store foundation, hardened by v0.28.1, and docs-cleaned by v0.28.2. M25 is implemented/released by v0.29.0 as deterministic local truth/evidence contracts. M26 is implemented/released by v0.30.0 as deterministic local grounded recall/context-pack contracts and hardened by v0.30.1. M27 is implemented/released by v0.31.0 as validation-only Tool Broker v2 contracts. M28 is implemented/released by v0.32.0 as Approval Authority v2 + Action Policy Expansion. M29 is implemented/released by v0.33.0 as Agent Task Planning Engine and hardened by v0.33.1. M30 is implemented/released by v0.34.0 as Multi-Step Execution Framework and hardened by v0.34.1. M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool. M32 is implemented/released by v0.36.0 and hardened by v0.36.1. M33 is implemented/released by v0.37.0 as First Safe Local File Read Proposal, Redacted Preview Only and hardened by v0.37.1 for redacted preview safety. M34-M40
remain planned/provisional until implemented by dedicated reviewed milestones.
