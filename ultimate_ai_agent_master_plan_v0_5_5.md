# Ultimate AI Agent Master Plan v0.5.5

Status: Active pre-coding baseline with local runtime, context survival, structured world state, and SDK/A2A adapter strategy incorporated.

## v0.5.5 Change Log — Local Runtime + Context Survival + SDK/A2A Boundaries

v0.5.5 accepts that useful local agents require infrastructure beyond model hosting. A local agent must manage fixed prompt/tool costs, runtime health, context windows, transcript trimming, exact world state, token calibration, and local resource constraints.

Added or updated:

```text
docs/canonical/53_structured_world_state.md
docs/canonical/54_context_budget_and_session_survival.md
docs/canonical/55_tool_result_retention_and_context_trimming.md
docs/canonical/56_prompt_tool_prefix_cache_policy.md
docs/canonical/57_local_runtime_and_offline_agent_infrastructure.md
docs/canonical/58_agent_sdk_and_a2a_adapter_strategy.md

docs/schemas/world_state.schema.json
docs/schemas/world_state_entry.schema.json
docs/schemas/world_state_snapshot.schema.json
docs/schemas/context_budget.schema.json
docs/schemas/context_trim_policy.schema.json
docs/schemas/context_trim_event.schema.json
docs/schemas/token_accounting.schema.json
docs/schemas/token_calibration_event.schema.json
docs/schemas/tool_result_retention_policy.schema.json
docs/schemas/prompt_bundle_manifest.schema.json
docs/schemas/tool_schema_bundle.schema.json
docs/schemas/prefix_cache_policy.schema.json
docs/schemas/local_runtime_manifest.schema.json
docs/schemas/local_model_profile.schema.json
docs/schemas/model_runtime_health.schema.json
docs/schemas/runtime_optimization_profile.schema.json
docs/schemas/local_resource_budget.schema.json
docs/schemas/privacy_routing_policy.schema.json
docs/schemas/agent_runtime_adapter_manifest.schema.json
docs/schemas/a2a_agent_card_minimal.schema.json

docs/evals/long_running_session_survival_eval.md
docs/evals/local_runtime_bypass_eval.md
docs/evals/local_model_capability_eval.md
docs/evals/local_json_mode_eval.md
docs/evals/local_tool_calling_eval.md
docs/evals/agent_sdk_adapter_boundary_eval.md
docs/evals/a2a_interop_contract_eval.md

docs/decisions/ADR-0045-use-structured-world-state.md
docs/decisions/ADR-0046-use-context-budget-manager.md
docs/decisions/ADR-0047-use-local-runtime-registry-and-resource-governor.md
docs/decisions/ADR-0048-use-agent-sdk-adapter-layer-and-a2a-gateway.md
```

New roadmap milestone:

```text
M2.5 — World State, Context Budget, Local Runtime, and SDK Adapter Boundaries
```

Core decision:

> The Ultimate AI Agent may use OpenAI Agents SDK, Claude Agent SDK, MCP, A2A, local runtimes, and cloud providers, but only through explicit adapters. The Python Agent Core remains the authority for contracts, consent, tool brokerage, event logging, redaction, memory/file writes, model routing, rollback, and verification.

---

## Historical Baseline v0.5.4

Status: Active pre-coding foundation baseline.

## Purpose

The Ultimate AI Agent is a Commander-led, spec-driven, memory-backed, relationship-aware AI operating system that turns vague goals into verified completed outcomes while remaining inspectable, permissioned, reversible, modular, scalable, and user-controlled.

v0.5.4 is a Runtime Hygiene Micro-Foundation release. It preserves v0.5.3's Claude remediation and adds small cross-cutting primitives that every later service should share.

## Source-of-truth rule

Canonical files define active truth. Versioned master plans are historical planning records.

```text
1. Current explicit user instruction
2. Active canonical files
3. Active feature spec
4. Accepted ADRs
5. Project memory
6. Historical master plans
7. Conversation history
```

The active roadmap is `docs/canonical/09_roadmap.md`. This master plan intentionally does not duplicate milestone definitions.

## v0.5.3 foundation retained

v0.5.3 already added:

```text
Verified Task Completion Framework
Durable execution ADR: custom event ledger + deterministic state machine first
Event-level cost attribution
Secret Broker + Provider Registry
Memory Retrieval V1
Autonomy Levels L0-L5
Minimum Lovable Kernel
Provisional Contract Policy
Trusted Computing Base
```

## v0.5.4 additions

v0.5.4 adds:

| Addition | Why it matters |
|---|---|
| Result and Error Envelope | Makes service responses consistent and debuggable. |
| Idempotency and Retry Policy | Prevents duplicate side effects when runs/tools are retried. |
| Actor/Authority Context | Records who or what initiated every meaningful operation. |
| Temporal Context and Freshness | Makes news, weather, memory, scanners, and reminders time-aware. |
| Data Classification Policy | Gives privacy, redaction, model routing, and logging a shared vocabulary. |
| Redaction and Safe Debugging | Prevents secrets/private data from leaking into prompts, logs, receipts, or debug bundles. |
| Service Boundaries and Dependency Injection | Protects the onion architecture from brittle internal coupling. |
| Capability Flags | Makes foundation-first blocking enforceable in code, not just docs. |
| Test Strategy v0 | Gives Codex/Hermes/agents consistent test categories and naming. |

## Runtime hygiene primitives

Every meaningful operation should carry or produce:

```text
result envelope
error envelope when applicable
actor context
temporal context
data classification
redaction metadata
idempotency key for mutable/retryable actions
trace_id / run_id / step_id / correlation_id
cost attribution when any model/tool/provider is used
rollback reference for mutable actions
```

## Foundation kernel

The Foundation Gate requires the following primitives before advanced modules:

```text
Execution Contract
Context Pack
Verified Task Completion contracts
Result/Error envelopes
Idempotency and retry policy
Actor/Authority context
Temporal/Freshness context
Data classification and redaction
Event Ledger and deterministic run state machine
Consent Ledger
Tool Broker
Secret Broker
Provider Registry
Model Router
Cost Governor
Memory Service and retrieval stack
File Manager
Rollback primitives
API boundary
Capability flags
Contract tests and shadow replay
Trusted Computing Base
```

## Advanced modules remain blocked

Do not build the following until the Foundation Gate passes:

```text
Reddit Scanner
News Scanner
Weather Module beyond safe provider-normalization prototype
Email Scanner
Message Scanner
Calendar Scanner
Companion proactivity
Skill Factory
Self-improving coding framework
Autopilot workflows
External high-autonomy execution
Provider-specific integrations that require credentials
```

## Implementation posture

Start with M0. Build validation scripts, stack skeleton, and runtime hygiene schemas. Preserve contracts as provisional until at least the Minimum Lovable Kernel exercises them. Do not add broad architecture modules after v0.5.4 unless a real M0/M1 implementation failure proves a gap.
