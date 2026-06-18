# Agent Module Maturity Map

Status: active review artifact. Baseline: v1.2.0-alpha. Assessed: 2026-06-18.

This audit maps common agent-system modules to what UAA actually has today. It is intentionally strict: a module gets credit for typed contracts, deterministic evaluators, tests, and bounded local/dev runtime behavior, but it does not get credit for roadmap ambition.

The machine-readable source is `docs/registry/agent_module_maturity_map.json`.
Verify it with:

```bash
.venv/bin/python scripts/verify_agent_module_maturity_map.py
```

## Maturity Scale

| Score | Level | Meaning |
| --- | --- | --- |
| 0 | Missing | No meaningful source, tests, or active documentation. |
| 1 | Declared only | Named in docs or old registries, but not maintained as current tested implementation. |
| 2 | Contract only | Typed contracts, metadata, or policy records exist, but no operating runtime behavior for the requested module. |
| 3 | Validated contract | Deterministic evaluators and tests exist, but behavior remains review-only or no-effect. |
| 4 | Constrained local runtime | A bounded local/dev runtime path exists and is tested, with explicit non-production authority limits. |
| 5 | Operational runtime | The module performs its intended runtime function in product workflows with durable integration and guardrails. |
| 6 | Production ready | Hardened for production authority, external integrations, observability, recovery, and operational use. |

No requested module is scored 5 or 6 in this audit.

## Direct Answer

| Module | UAA has it? | Score | Where it lives | Honest read | Main missing pieces |
| --- | --- | ---: | --- | --- | --- |
| Agent runtime skeleton | Partially | 4 | `src/ultimate_ai_agent/core/kernel/runner.py`, `src/ultimate_ai_agent/core/kernel/requests.py`, `src/ultimate_ai_agent/core/kernel/results.py` | `MinimumKernelRunner` coordinates typed requests, contracts, consent, approval, tool-broker evaluation, local/dev file write or rollback, memory refs, ledger events, world state, and receipts. | General agent loop, model reasoning loop, arbitrary tools, production authority. |
| Orchestration layer | Fragmented | 3 | `src/ultimate_ai_agent/core/kernel/runner.py`, `src/ultimate_ai_agent/core/orchestration_efficiency/planner.py` | UAA has a narrow kernel flow and no-effect orchestration efficiency previews. This is not a full Commander-style orchestrator. | Durable full-flow orchestration across prompts, tools, memory, APIs, workflows, and sub-agents. |
| Decision router | Fragmented | 2 | `src/ultimate_ai_agent/core/model_router/router.py`, `src/ultimate_ai_agent/core/recall/router.py`, `src/ultimate_ai_agent/core/truth/router.py`, `src/ultimate_ai_agent/core/tools/broker.py` | Strong specialized routers exist, especially model routing, recall routing, truth routing, and tool decisions. There is no single router matching the requested "answer/tool/memory/human/workflow" role. | Top-level path selection, unified decision trace, workflow escalation trigger. |
| Planning module | Yes, review-only | 3 | `src/ultimate_ai_agent/core/planning/contracts.py`, `src/ultimate_ai_agent/core/planning/planner.py` | Task planning contracts validate explicit goals, steps, dependencies, safety boundaries, and non-authoritative receipts. | Plan generation from vague goals, adaptive replanning, progress-driven updates. |
| Task decomposition module | Contract substrate only | 2 | `src/ultimate_ai_agent/core/planning/goals.py`, `src/ultimate_ai_agent/core/planning/steps.py`, `src/ultimate_ai_agent/core/planning/dependencies.py` | UAA can represent decomposed tasks, but callers/tests supply the decomposition. | Vague-request parser, subtask generator, decomposition-quality checks. |
| Workflow engine | No-effect only | 3 | `src/ultimate_ai_agent/core/execution/state_machine.py`, `src/ultimate_ai_agent/core/execution/runs.py`, `src/ultimate_ai_agent/core/execution/steps.py` | The execution framework models multi-step runs, dependencies, transitions, replay protection, and no-effect completion. It does not run real workflows. | Actual workflow runner, scheduler, persistence, tool execution, send/deliver actions. |
| State manager | Fragmented | 3 | `src/ultimate_ai_agent/core/world_state/models.py`, `src/ultimate_ai_agent/core/world_state/snapshots.py`, `src/ultimate_ai_agent/core/ledger/run_state.py` | World state, run state, execution state, and ledger pieces exist and are tested in bounded domains. | Unified live state manager for attempts, retries, active work, and resumption. |
| Context manager | Yes, no injection | 3 | `src/ultimate_ai_agent/core/contracts/context_pack.py`, `src/ultimate_ai_agent/core/recall/context_pack.py`, `src/ultimate_ai_agent/core/context_budget/trimming.py`, `src/ultimate_ai_agent/core/context_handoff/workflow.py` | UAA has safe context packs, grounded recall selection, context-budget trimming, proposals, and handoff approval contracts. | Live context-window manager and context injection into model sessions. |
| Tool registry | Yes, bounded | 4 | `src/ultimate_ai_agent/core/tools/registry.py`, `src/ultimate_ai_agent/core/tools/broker.py`, `src/ultimate_ai_agent/core/tools/runtime/invocation.py` | Tool manifests, registry, broker, consent/approval checks, and allowlisted runtime adapters exist. Arbitrary dynamic dispatch is denied. | General tool execution runtime, plugin marketplace authority, arbitrary callable loading. |
| Capability registry | Stale partial | 1 | `docs/canonical/32_capability_registry_and_dependency_graph.md`, `docs/registry/capability_registry_v0_5_8.json`, `docs/registry/dependency_graph_v0_5_3.md` | The concept is documented, but the maintained artifacts lag the active baseline and are not a complete current module capability source of truth. | Active-baseline registry, code-owned capability decisions, complete module capability and maturity inventory. |
| Multi-agent coordinator | Contract only | 2 | `src/ultimate_ai_agent/core/adapters/a2a_manifest.py`, `src/ultimate_ai_agent/core/production_readiness/remote_agent_coordination.py`, `src/ultimate_ai_agent/core/remote_workers/dry_run.py` | UAA has inert A2A metadata, remote-agent coordination contracts, and dry-run remote worker records. Live dispatch, agent spawn, network coordination, and remote execution are denied. | Peer communication, task assignment, agent spawning, inter-agent bus, remote execution authority. |
| Human-in-the-loop module | Partially | 4 | `src/ultimate_ai_agent/core/approvals/authority.py`, `src/ultimate_ai_agent/core/file_review/approval_capture.py`, `src/ultimate_ai_agent/core/autonomy/human_checkpoint_scheduling.py` | UAA has local approval requests, grants, revocation, exact-scope validation, tool/model route approval integration, and review-only checkpoint contracts. | General clarification loop, product approval queue as authority, real checkpoint scheduling or notifications. |

## What UAA Is Strong At

- Contract-first safety boundaries.
- Deterministic evaluators.
- No-effect and review-only state transitions.
- Exact-scope approvals for bounded local/dev flows.
- Tool, context, planning, execution, and recall contracts with tests.

## What UAA Is Missing

- A current active-baseline capability registry.
- A top-level decision router.
- A real task decomposition engine.
- A full orchestration/workflow runtime.
- A live multi-agent coordinator.
- A product-grade state service.
- Production authority for agent autonomy, external dispatch, browser/tool/plugin execution, or model/provider authority.

## Keeping This Honest

Update `docs/registry/agent_module_maturity_map.json` whenever a module changes maturity. Do not raise a maturity score unless there are source paths, docs, and tests that prove the new level. The verifier rejects unknown maturity labels, missing requested modules, and references to missing files.
