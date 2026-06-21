# UAA-P1-062 Local Model Manager / Memory-Aware Runtime Control

Status: docs-only lane shape
Baseline: v0.102.3 / 0.102.3
Parent roadmap: `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md` M170

UAA-P1-062 shapes the governed Local Model Manager lane. It does not implement
routes, CLI commands, process control, lifecycle actions, model switching,
identity updates, downloads, provider/model calls, web fetching, dependencies,
OpenWebUI authority, Control Center authority, or runtime behavior.

## Product Principle

Python Agent Core owns local model truth. Control Center and OpenWebUI render
state and request governed actions only. No UI surface may become the authority
for model discovery, memory-fit planning, lifecycle state, switch receipts,
identity updates, safe-disable, or rollback.

## Future Interface Shape

| Surface | Future role | Current UAA-P1-062 posture |
|---|---|---|
| Core | `src/ultimate_ai_agent/core/local_model_management/` owns discovery, memory-fit planning, lifecycle planning, receipts, rollback, and redaction rules. | Planned/blocked. No new core runtime behavior in this milestone. |
| API | FastAPI runtime/local-model readiness and lifecycle contracts expose backend-owned state. | Planned/blocked. No routes or OpenAPI changes in this milestone. |
| CLI | Future `uaa local-model status/start/stop/switch`; switch supports dry-run first. | Planned/blocked. No CLI commands in this milestone. |
| Control Center | Runtime/Settings surfaces render installed/current/fit/lifecycle/readiness state and request governed actions. | Planned/blocked. No frontend behavior in this milestone. |
| OpenWebUI | Shell over exposed model identity/status, never authority. | Planned/blocked. No OpenWebUI config or runtime changes in this milestone. |

## Staged Lane

1. Cleanup and consolidation:
   Tighten existing local-model scripts/docs, remove throwaway helpers, split
   oversized modules only under a later scoped cleanup task, and preserve
   current M160-M167 safety gates.
2. Read-only model status:
   Define backend-owned installed GGUF refs, current loaded-model status,
   memory/VRAM fit posture, disk size refs, port state, llama.cpp health, and
   redacted status/log refs.
3. Approval-bound start/stop:
   Add lifecycle proposals only after exact backend contracts, route side-effect
   classes, CLI parity, LocalApprovalAuthority scopes, receipts, rollback, and
   safe-disable behavior are accepted.
4. Dry-run switch planner:
   Plan selected model, RAM/VRAM/context impact, current-model unload posture,
   one-big-model guard, expected alias, identity update plan, and rollback plan
   without executing the switch.
5. Executable switch:
   Stop current server, start selected model, verify health and model identity,
   update UAA/OpenWebUI identity, emit redacted evidence, and preserve rollback.
   This stage requires a later exact scoped milestone.
6. Downloads/acquisition:
   Add search/download only after switching is solid and separately approved.

## Required Contracts Before Runtime Work

- backend-owned installed GGUF status contract
- current loaded-model status contract
- memory-fit planner contract
- llama.cpp lifecycle status contract
- exact approval scopes for start, stop, switch, identity update, and rollback
- one-big-model enforcement policy
- redacted receipt and evidence format
- rollback and safe-disable plan
- CLI parity for every operator-relevant action
- route side-effect classification and OpenAPI tests for any route change
- product-language rules for loaded, running, switched, and identity-updated
  claims

## Non-Goals For This Milestone

- no backend routes
- no OpenAPI operation changes
- no CLI commands
- no process control
- no start, stop, switch, identity update, download, or rollback execution
- no provider/model calls
- no web fetching
- no new dependencies
- no OpenWebUI runtime/config changes
- no Control Center controls or React-only authority
- no public release or production-readiness claim

## Completion Gate For UAA-P1-062

UAA-P1-062 is complete when this lane shape is documented, active roadmap and
board truth say runtime stages remain blocked, product truth points to this
scope, and documentation/product-truth/reconciliation checks pass.

Future implementation stages need later documented scope. Do not reuse
UAA-P1-062 as authority to implement lifecycle, switching, downloads, routes,
CLI commands, or process control.
