# UAA-P2 Agent Runtime Compatibility Prompts

Status: reusable Codex execution prompt pack

This file turns the OpenAI Agents SDK architecture review into an ordered,
repo-safe implementation sequence for UAA. It is a prompt library, not runtime
configuration. It grants no backend routes, provider SDK calls, live web,
browser automation, shell/subprocess execution, connector writes, memory
writes, context injection, broad action execution, public beta, public release,
or production authority.

The objective is not to adopt the OpenAI Agents SDK as UAA's architecture. The
objective is to make UAA's Python Agent Core compatible with agent-runtime
patterns while preserving UAA-owned policy, approvals, receipts, audit,
memory, evidence, replay, rollback, and provider neutrality.

## Operator Use

Run the prompts in order. Each prompt is intentionally scoped so the sequence
can stop after any step with a useful artifact. Do not skip safety review,
tests, docs, or product-truth alignment.

If a prompt discovers that a required concept already exists, it should harden
or document the existing implementation instead of creating a parallel system.

## E2E Driver Prompt

Copy this prompt into Codex to run the whole file end to end:

```text
You are working in /Users/sambehdjou/Documents/GitHub/ultimate-ai-agent.

Read and execute docs/codex/UAA_P2_AGENT_RUNTIME_COMPATIBILITY_PROMPTS.md end
to end, in order. Treat the file as an ordered implementation prompt pack.

Hard constraints:
- Follow AGENTS.md and all repository invariants.
- Preserve Python Agent Core as the authority boundary.
- Do not adopt the OpenAI Agents SDK as core architecture.
- Do not add runtime model calls, provider SDK calls, live web fetching,
  browser automation, unrestricted shell/subprocess execution, connector
  writes, memory writes, context injection, plugin runtime import, public beta,
  public release, production authority, or broad autonomy.
- Keep each change contract-first, local-first, provider-neutral, approval
  bound, auditable, rollback-aware, redacted, and tested.
- If existing code/docs already implement a requested primitive, reuse and
  harden it rather than creating a competing abstraction.

Execution rules:
- Work prompt by prompt.
- Before edits, read the named source files and inspect matching code/tests.
- After each prompt, run the focused tests or verifier named by that prompt
  when available.
- If a prompt requires authority the current repo does not grant, stop that
  prompt, record the blocker, and continue only if the next prompt can remain
  docs-only or contract-only.
- Update the smallest relevant docs and indexes.
- Final response must list files changed, tests/verifiers run, skipped checks
  with reasons, blocked items, and the next safest prompt to run if the full
  sequence was not completed.
```

## Prompt 0: Baseline Discovery And Scope Lock

```text
You are working only in ultimate-ai-agent.

Task: establish the current baseline for UAA-P2 Agent Runtime Compatibility
without making code changes.

Read first:
- AGENTS.md
- README.md
- VERSION.md
- docs/README.md
- docs/DOCUMENTATION_INDEX.md
- docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md
- docs/capability_registry.md
- docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md
- docs/kanban/current_board.md
- docs/kanban/founder_command_center_board.md
- docs/control_center/OPERATOR_SHELL_GAP_MAP.md
- docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md

Inspect code/tests for:
- CapabilityManifest, CapabilityRegistry, Coordinator, CoordinationMode
- ToolBroker, PolicyEngine, LocalApprovalAuthority
- task decomposition contracts and runtime
- durable runs, receipts, evidence, handoffs, and approval refs
- existing OpenAI/MCP/A2A schema export helpers

Deliverable:
- A short implementation note in your final response only. Do not edit files.
- Identify which requested primitives already exist, which need hardening, and
  which should remain future-scoped.

Hard boundaries:
- no edits
- no web fetching
- no provider SDK calls
- no runtime calls
- no new dependencies

Validation:
- git status --short
```

## Prompt 1: Architecture Charter And Roadmap Placement

```text
You are working only in ultimate-ai-agent.

Task: add a contract-first architecture charter for UAA-P2 Agent Runtime
Compatibility.

Goal: document the target layer as an adapter and compatibility boundary, not
as a new authority layer or OpenAI Agents SDK adoption.

Read first:
- docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md
- docs/capability_registry.md
- docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md
- docs/kanban/current_board.md
- docs/kanban/founder_command_center_board.md
- docs/control_center/OPERATOR_SHELL_GAP_MAP.md
- docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md

Required artifact:
- docs/architecture/UAA_P2_AGENT_RUNTIME_COMPATIBILITY.md

The charter must define:
- why UAA should borrow agent patterns but not adopt an SDK as the kernel
- AgentRuntimeAdapter as a future execution target boundary
- capability manifests as the single tool/agent/workflow registry language
- UAA-owned trace, receipt, audit, replay, and memory truth
- structured handoff envelopes
- single orchestrator first, specialists later
- no-authority posture for this charter
- explicit non-goals

Update the smallest relevant indexes if safe:
- docs/README.md
- docs/DOCUMENTATION_INDEX.md
- docs/kanban/current_board.md only if the board already has an appropriate
  future/P2 planning section

Hard boundaries:
- docs-only
- no backend routes
- no frontend controls
- no code
- no provider SDK calls
- no web fetching
- no runtime authority

Validation:
.venv/bin/python scripts/verify_documentation_integrity.py
git diff --check
```

## Prompt 2: Capability Manifest Metadata Hardening

```text
You are working only in ultimate-ai-agent.

Task: harden CapabilityManifest metadata for agent-runtime compatibility while
preserving existing behavior.

Goal: make every future tool, agent, workflow, reviewer, human gate, and
runtime adapter describable through UAA-owned authority metadata.

Read first:
- docs/capability_registry.md
- src/ultimate_ai_agent/core/capabilities/models.py
- src/ultimate_ai_agent/core/capabilities/enums.py
- src/ultimate_ai_agent/core/capabilities/registry.py
- src/ultimate_ai_agent/core/capabilities/policy.py
- tests/test_capability_registry.py
- tests/test_capability_registry_coordinator.py

Implement only if the fields do not already exist. Add backward-compatible
optional/defaulted metadata for:
- authority_level
- approval_required
- deterministic
- rollback_supported
- receipt_required
- privacy_level
- estimated_latency_class
- estimated_cost_class
- evidence_required
- memory_write_allowed, default false
- context_injection_allowed, default false
- provider_runtime_allowed, default false
- browser_runtime_allowed, default false
- connector_write_allowed, default false

Rules:
- Defaults must preserve current tests and fail closed for authority flags.
- Do not add live adapters, routes, provider calls, web calls, memory writes,
  or context injection.
- Update docs/capability_registry.md examples and tests.

Validation:
PYTHONPATH=src .venv/bin/python -m pytest tests/test_capability_registry.py tests/test_capability_registry_coordinator.py -q
PYTHONPATH=src .venv/bin/python scripts/dev/capability_registry_smoke.py
.venv/bin/python scripts/verify_documentation_integrity.py
git diff --check
```

## Prompt 3: AgentRuntimeAdapter Contract Shell

```text
You are working only in ultimate-ai-agent.

Task: add a provider-neutral AgentRuntimeAdapter contract shell.

Goal: represent local LLMs, deterministic workers, Codex-like tools,
OpenAI-style agent runtimes, Anthropic-style runtimes, and future frameworks as
execution targets behind UAA contracts. This is a contract shell only.

Read first:
- docs/architecture/UAA_P2_AGENT_RUNTIME_COMPATIBILITY.md
- docs/capability_registry.md
- src/ultimate_ai_agent/core/capabilities/
- src/ultimate_ai_agent/core/task_decomposition/
- src/ultimate_ai_agent/core/execution/durable_runs.py
- src/ultimate_ai_agent/core/providers/
- tests/test_capability_registry_coordinator.py

Required artifacts:
- src/ultimate_ai_agent/core/agent_runtime/
- tests/test_agent_runtime_adapter_contract.py
- docs/architecture/UAA_P2_AGENT_RUNTIME_COMPATIBILITY.md updates

Define typed contracts for:
- AgentRuntimeKind
- AgentRuntimeAuthorityPosture
- AgentRuntimeRequest
- AgentRuntimeDecision
- AgentRuntimeResult
- AgentRuntimeTraceRef
- AgentRuntimeAdapter protocol or base class
- deterministic no-op/local fixture adapter for tests only

The contract must prove:
- UAA owns policy, approval, receipts, audit, and memory
- adapter output is not authority
- adapter traces are imported evidence refs only, not system truth
- raw prompt, raw response, raw provider payload, raw path, raw logs,
  environment dumps, credentials, and secret-like values are rejected or absent
- provider SDK and network execution are not implemented

Hard boundaries:
- no provider SDK imports
- no network calls
- no live model calls
- no backend routes
- no Control Center controls
- no memory writes
- no context injection
- no connector writes
- no shell/browser execution

Validation:
PYTHONPATH=src .venv/bin/python -m pytest tests/test_agent_runtime_adapter_contract.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_capability_registry_coordinator.py -q
.venv/bin/python scripts/verify_documentation_integrity.py
git diff --check
```

## Prompt 4: Structured Handoff Envelope

```text
You are working only in ultimate-ai-agent.

Task: define a reusable structured handoff envelope for specialists and future
agent runtime adapters.

Goal: replace freeform agent-to-agent handoff assumptions with explicit,
auditable, safe-ref contracts.

Read first:
- docs/architecture/UAA_P2_AGENT_RUNTIME_COMPATIBILITY.md
- docs/capability_registry.md
- docs/control_center/PRODUCT_LOOP_009_CHAT_TO_LOOP_HANDOFF.md
- src/ultimate_ai_agent/core/chat/
- src/ultimate_ai_agent/core/context_handoff/
- src/ultimate_ai_agent/core/storage/founder_loop.py
- tests/test_chat_to_loop_handoff_v1.py
- tests/test_context_handoff_approval_contracts.py

Required artifacts:
- src/ultimate_ai_agent/core/agent_runtime/handoffs.py or equivalent local
  contract module
- tests/test_agent_runtime_handoff_envelope.py
- docs/architecture/UAA_P2_AGENT_RUNTIME_COMPATIBILITY.md updates

Define a HandoffEnvelope with:
- handoff_ref
- source_turn_ref or source_run_ref
- source_capability_ref
- target_capability_ref
- objective_ref
- safe_objective_summary
- allowed_authority_refs
- blocked_authority_refs
- evidence_refs
- receipt_refs
- expected_output_schema_ref
- timeout_policy_ref
- idempotency_ref
- rollback_or_safe_disable_ref
- human_review_required
- execution_authorized, default false
- memory_write_authorized, default false
- context_injection_authorized, default false
- connector_write_authorized, default false

Rules:
- Safe refs and summaries only.
- No raw prompt/response/provider payload storage.
- Handoff approval is not execution approval.
- Handoff envelopes may be reviewable proposals only unless a later scoped
  milestone grants exact execution authority.

Validation:
PYTHONPATH=src .venv/bin/python -m pytest tests/test_agent_runtime_handoff_envelope.py tests/test_chat_to_loop_handoff_v1.py tests/test_context_handoff_approval_contracts.py -q
.venv/bin/python scripts/verify_documentation_integrity.py
git diff --check
```

## Prompt 5: UAA-Owned Trace And Receipt Span Contract

```text
You are working only in ultimate-ai-agent.

Task: define UAA-owned agent runtime trace span contracts.

Goal: allow future SDK/runtime traces to be represented as subordinate evidence
inside UAA without making vendor tracing the source of truth.

Read first:
- docs/architecture/UAA_P2_AGENT_RUNTIME_COMPATIBILITY.md
- src/ultimate_ai_agent/core/execution/durable_runs.py
- src/ultimate_ai_agent/core/ledger/
- src/ultimate_ai_agent/core/storage/founder_loop.py
- src/ultimate_ai_agent/core/providers/invocation.py
- tests covering durable runs, receipts, provider invocation receipts, and
  evidence timeline

Required artifacts:
- src/ultimate_ai_agent/core/agent_runtime/tracing.py or equivalent local
  contract module
- tests/test_agent_runtime_trace_contract.py
- docs/architecture/UAA_P2_AGENT_RUNTIME_COMPATIBILITY.md updates

Define trace contracts for:
- AgentRuntimeTraceSpan
- AgentRuntimeTraceEvent
- AgentRuntimeImportedVendorTrace
- AgentRuntimeReceiptPlan

Required semantics:
- UAA trace refs are canonical.
- Vendor trace IDs are optional evidence metadata only.
- Trace spans carry safe summaries, refs, timing class, result status, policy
  status, approval status, receipt refs, and blocked authority refs.
- Raw content fields are not allowed.
- Trace import never grants authority and never bypasses LocalApprovalAuthority.

Validation:
PYTHONPATH=src .venv/bin/python -m pytest tests/test_agent_runtime_trace_contract.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_execution_receipt_plan.py tests/test_kernel_rollback.py -q
.venv/bin/python scripts/verify_documentation_integrity.py
git diff --check
```

## Prompt 6: Static Schema Export Compatibility

```text
You are working only in ultimate-ai-agent.

Task: add or harden static schema export compatibility for OpenAI-style tools,
MCP tools, and A2A-style agent cards.

Goal: make UAA capability manifests exportable to common agent ecosystem schema
shapes without importing SDKs or creating live dispatch.

Read first:
- docs/capability_registry.md
- src/ultimate_ai_agent/core/capabilities/registry.py
- src/ultimate_ai_agent/core/capabilities/models.py
- tests/test_capability_registry.py

Required artifacts:
- tests that prove schema export is static and no-dispatch
- docs/capability_registry.md updates
- optional script update only if an existing smoke/export script already
  covers capability schemas

Rules:
- No OpenAI SDK dependency.
- No MCP client runtime.
- No A2A runtime dispatch.
- No network calls.
- No provider calls.
- Exports must include blocked authority and safety metadata where the target
  schema has no equivalent, using UAA-owned extension metadata.
- Imports from external metadata must remain inert until a local reviewed
  manifest and adapter are registered.

Validation:
PYTHONPATH=src .venv/bin/python -m pytest tests/test_capability_registry.py tests/test_capability_registry_coordinator.py -q
PYTHONPATH=src .venv/bin/python scripts/dev/capability_registry_smoke.py
.venv/bin/python scripts/verify_documentation_integrity.py
git diff --check
```

## Prompt 7: Deterministic Specialist Demo

```text
You are working only in ultimate-ai-agent.

Task: add a deterministic in-process specialist demo for agent-runtime
compatibility.

Goal: prove single orchestrator -> specialist-as-tool -> artifact -> receipt
semantics without external runtimes.

Read first:
- docs/architecture/UAA_P2_AGENT_RUNTIME_COMPATIBILITY.md
- docs/capability_registry.md
- src/ultimate_ai_agent/core/capabilities/
- src/ultimate_ai_agent/core/agent_runtime/ if present
- tests/test_capability_registry_coordinator.py

Required behavior:
- Register one deterministic in-process read-only specialist capability.
- The specialist receives a structured envelope, returns a safe artifact, emits
  UAA trace/receipt refs, and cannot execute, write memory, inject context,
  call providers, fetch web, use browser automation, or write connectors.
- Coordinator remains the planner and final synthesizer.

Required artifacts:
- focused tests
- smoke script update only if the existing capability registry smoke harness is
  the right home
- docs update explaining this is a local deterministic compatibility demo only

Hard boundaries:
- no external process
- no provider SDK
- no model call
- no web/network
- no backend route
- no frontend control
- no new dependency

Validation:
PYTHONPATH=src .venv/bin/python -m pytest tests/test_capability_registry_coordinator.py tests/test_agent_runtime_adapter_contract.py tests/test_agent_runtime_handoff_envelope.py tests/test_agent_runtime_trace_contract.py -q
PYTHONPATH=src .venv/bin/python scripts/dev/capability_registry_smoke.py
.venv/bin/python scripts/verify_documentation_integrity.py
git diff --check
```

## Prompt 8: Founder Command Center Product Surface Mapping

```text
You are working only in ultimate-ai-agent.

Task: map agent-runtime compatibility into the Founder Command Center product
language without adding UI controls or authority.

Goal: make the operator-facing story clear: UAA can host future agent runtimes
as governed capabilities, but the Control Center remains a shell and the Python
Agent Core remains authority.

Read first:
- docs/architecture/UAA_P2_AGENT_RUNTIME_COMPATIBILITY.md
- docs/control_center/PRODUCT_LANGUAGE_RULES.md
- docs/control_center/OPERATOR_SHELL_GAP_MAP.md
- docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md
- docs/kanban/current_board.md
- docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md

Deliverables:
- update the smallest relevant docs so the compatibility layer is described as
  planned/contract-only or implemented-contract-only, whichever is true
- ensure no product copy claims OpenAI Agents adoption, production readiness,
  broad autonomy, live providers, live web, connector writes, memory writes, or
  context injection

Hard boundaries:
- docs/product-language only
- no routes
- no frontend controls
- no runtime behavior

Validation:
.venv/bin/python scripts/verify_documentation_integrity.py
git diff --check
```

## Prompt 9: Verification And Static Guardrails

```text
You are working only in ultimate-ai-agent.

Task: add or harden verification for the agent-runtime compatibility boundary.

Goal: make regression obvious if future work accidentally adds provider SDK
imports, live web, browser automation, connector writes, memory writes, context
injection, raw payload storage, or authority claims to the compatibility layer.

Read first:
- scripts existing verify_* files relevant to capability registry, docs
  integrity, provider invocation, web access, and Foundation Gate
- src/ultimate_ai_agent/core/gate/
- tests touching gate/evaluator characterization
- docs/architecture/UAA_P2_AGENT_RUNTIME_COMPATIBILITY.md

Required artifact:
- a focused verifier script or Foundation Gate check only if it fits existing
  patterns and can stay scoped
- focused tests for the verifier/check

Verifier should scan for:
- OpenAI SDK or other provider SDK imports in the compatibility layer
- requests/httpx/urllib/playwright/selenium/browser automation imports
- raw prompt/raw response/raw provider payload fields
- authority flags defaulting true
- direct runtime dispatch routes
- memory_write_authorized or context_injection_authorized defaults true

Hard boundaries:
- no live execution
- no network
- no provider calls
- no broad grep-only false positives that block unrelated existing approved
  lanes

Validation:
PYTHONPATH=src .venv/bin/python -m pytest <focused verifier tests> -q
PYTHONPATH=src .venv/bin/python <new verifier script>
.venv/bin/python scripts/verify_documentation_integrity.py
git diff --check
```

## Prompt 10: Final E2E Review And PR-Ready Summary

```text
You are working only in ultimate-ai-agent.

Task: perform final review of the UAA-P2 Agent Runtime Compatibility sequence.

Read:
- all changed files
- docs/architecture/UAA_P2_AGENT_RUNTIME_COMPATIBILITY.md if created
- docs/capability_registry.md if changed
- tests and scripts changed in this sequence

Review checklist:
- No SDK became the core architecture.
- Python Agent Core still owns authority.
- Compatibility adapters are inert unless exact local authority exists.
- Capability metadata fails closed.
- Handoffs are safe-ref, auditable, and non-executing by default.
- Trace import is evidence only.
- Memory remains recall, not truth or authority.
- Product language distinguishes implemented, partial, planned, blocked, and
  missing states.
- OpenAPI, /api/manifest, route side-effect classes, and Foundation Gate
  boundaries were not bypassed.
- Dirty worktree changes from other work were not reverted.

Run the broadest safe checks feasible:
PYTHONPATH=src .venv/bin/python -m pytest tests/test_capability_registry.py tests/test_capability_registry_coordinator.py -q
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
git diff --check

Final response must include:
- files changed
- tests and verifiers run
- checks skipped with reasons
- blocked items
- whether the sequence stayed within no-new-authority scope
- recommended next prompt or milestone
```
