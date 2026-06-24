# UAA-P1-089 Top-Level Decision Router Contract

Status: implemented contract/read-model lane only.
Baseline: `v0.104.0`.

`UAA-P1-089` defines a unified top-level decision router contract so UAA can
represent route outcome proposals across the existing strong modules without
granting route authority. It makes the system easier to inspect as one agent
loop while preserving the hard boundary that this lane performs no action.

The contract lives in:

```text
src/ultimate_ai_agent/core/decision_router/
```

## Outcome Kinds

The contract models these route outcome proposals:

- `answer_directly`
- `use_reviewed_memory`
- `propose_action_inbox_item`
- `ask_human`
- `escalate_to_review`
- `defer`
- `blocked_unsafe`
- `insufficient_evidence`

These are read-model outcomes only. They do not execute, authorize, dispatch,
retrieve hidden context, write memory, call tools, call models, call providers,
start workflows, open a browser, access the network, run shell/subprocesses, or
write connectors.

## Typed Models

- `DecisionRouterInput`
- `DecisionRouterCandidate`
- `DecisionRouterOutcome`
- `DecisionRouterTrace`
- `DecisionRouterBlockedState`

Each outcome carries:

- safe reason refs
- evidence refs
- source refs
- blocked authority refs
- confidence and ambiguity posture
- next safe operator action
- downstream proposal refs when the outcome is `propose_action_inbox_item`
- blocked states for unsafe or insufficient-evidence outcomes
- no-effect proof flags

## Module Binding

The top-level contract binds existing modules by reference only:

| Module area | Binding posture |
|---|---|
| Memory | May point to reviewed memory/read-model refs; no memory write or context injection. |
| Plans | May point to plan refs or propose later decomposition work; no execution. |
| Actions | May point to Action Inbox proposal refs; no action execution or approval capture. |
| Evidence | May point to Evidence Timeline refs; no evidence mutation. |
| Approvals | Approval refs are identifiers/evidence only; no approval authority is granted. |
| Tool broker | Tool decisions may be cited as refs; no broker call or tool execution. |
| Human-in-the-loop | Ask-human/escalate/defer outcomes are review posture only. |

## Safety Boundary

Every candidate, trace, and outcome includes blocked authority refs for:

```text
no runtime model call
no provider call
no tool execution
no action execution
no workflow execution
no memory write
no context injection
no shell/subprocess
no browser/network
no connector write
```

The contract also records explicit no-effect flags such as
`route_authority_granted=false`, `execution_performed=false`,
`no_model_call_performed=true`, `no_tool_execution_performed=true`,
`no_workflow_execution_performed=true`, `no_memory_write_performed=true`, and
`no_context_injection_performed=true`.

Refs from model output, runtime output, OpenWebUI output, or context packs are
not accepted as route authority source refs. If those artifacts matter, a later
lane must represent them as evidence or blocked states with explicit review
posture.

## Determinism

`route_decision()` is deterministic and no-effect:

1. If no candidates exist, it emits `insufficient_evidence`.
2. If any `blocked_unsafe` candidate exists, it emits a blocked outcome first.
3. Otherwise it ranks by confidence, then stable outcome priority, then
   candidate ref.

This function is a read-model helper, not a live runtime router. It inspects
only the provided bounded safe refs and candidate fixtures.

## Non-Goals

This lane does not add:

- FastAPI routes
- Control Center controls
- runtime model calls
- provider SDK calls
- web fetching
- browser automation
- shell/subprocess execution
- connector writes
- memory writes
- context injection
- action execution
- workflow execution
- autonomous routing authority
- production/public beta claims

## Verification

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_uaa_p1_089_top_level_decision_router_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_uaa_p1_089_top_level_decision_router_contract.py -q
```
