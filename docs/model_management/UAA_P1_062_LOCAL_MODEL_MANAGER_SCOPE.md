# UAA-P1-062 Local Model Manager / Memory-Aware Runtime Control

Status: docs-only lane shape
Baseline: v0.103.0 / 0.103.0
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

## Candidate Implementation Roadmap

The next implementation milestones should preserve this order. These items are
roadmap shape only until later exact scoped milestones grant implementation
authority.

1. Read-only inventory:
   Build Python-core inventory over the consolidated local model root such as
   `$HOME/Models`. Detect GGUF, MLX/Hugging Face cache, Ollama, and LM Studio
   candidates. Return safe model refs, runtime type, size bucket, role hints,
   and explicit `runnable_now`, `needs_adapter`, or `blocked` status.
2. CLI first:
   Add `uaa local-model status`, `uaa local-model list`, and
   `uaa local-model inspect <model-ref>` before any UI controls or lifecycle
   actions. No switching or process control is allowed in this stage.
3. Control Center read-only UI:
   Replace the blocked Models surface with a backend-owned read-only table for
   installed, runnable, active, blocked, needs-adapter, and memory-posture
   states. Do not expose a start, stop, switch, activate, or settings mutation
   control in this stage.
4. llama.cpp router mode:
   Add governed GGUF-only lifecycle planning around
   `llama-server --models-dir <approved-gguf-cache-ref> --models-max 1`.
   Enforce one-heavy-model policy and verify `/health`, `/v1/models`, and
   active model identity before any later lifecycle claim.
5. Dry-run switch planner:
   Add `uaa local-model switch --to <model-ref> --dry-run`. The plan must name
   current model posture, target model ref, memory risk, alias, loopback
   endpoint ref, rollback plan, safe-disable plan, and exact approval scope
   required. It must not start, stop, unload, or load a model.
6. Approval-bound switch:
   Add executable switch only after dry-run contracts pass. The command shape is
   `uaa local-model switch --to <model-ref> --approval-ref <ref>`. It must emit
   a redacted receipt, validate exact LocalApprovalAuthority scope, verify
   health and model identity, and preserve rollback.
7. Desktop/Hermes UI control:
   Add an `Activate` or equivalent control only after CLI/API behavior is safe
   and tested. The UI requests governed Python-core actions only; React state
   never owns model truth, lifecycle, identity, approval, or rollback state.
8. MLX/Ollama/LM Studio later:
   Add MLX, Ollama, and LM Studio adapters only after the GGUF path is solid.
   MLX/Hugging Face cache entries remain installed-but-needs-adapter until an
   approved MLX runner/server contract exists.

## Implementation Prompt For Later Scoped Milestone

Use this prompt when creating the next exact scoped milestone. Do not treat this
prompt as implementation authority by itself.

```text
Implement UAA-P1-064 Local Model Inventory Read-Only Backend + CLI.

Scope:
- Build Python Agent Core inventory for consolidated local model roots such as
  $HOME/Models/huggingface, $HOME/Models/llama.cpp/model-cache,
  $HOME/Models/ollama, $HOME/Models/lm-studio, and $HOME/Models/mlx.
- Detect GGUF, MLX/Hugging Face cache, Ollama manifest, and LM Studio candidate
  records.
- Return safe model refs, runtime family, runnable status, needs-adapter status,
  blocked reason refs, size buckets, role hints, source class, and memory-posture
  summary refs without durable raw local paths.
- Add CLI parity first: uaa local-model status, uaa local-model list, and
  uaa local-model inspect <model-ref>.
- Add tests and docs proving no model calls, no downloads, no process control,
  no provider calls, no web fetching, no raw path evidence, and no Control
  Center authority.

Out of scope:
- no start/stop/switch
- no llama-server lifecycle
- no OpenAPI route unless separately accepted with side-effect classification
- no Control Center mutation controls
- no MLX/Ollama/LM Studio runtime start
- no model/provider output authority
```

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

## Verification

```bash
.venv/bin/python scripts/verify_uaa_p1_062_local_model_manager_scope.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_uaa_p1_062_local_model_manager_scope.py
```

The verifier is inspection-only. It checks that active docs, product truth,
gap maps, board state, and reconciliation artifacts preserve the docs-only
scope and keep runtime stages blocked.
