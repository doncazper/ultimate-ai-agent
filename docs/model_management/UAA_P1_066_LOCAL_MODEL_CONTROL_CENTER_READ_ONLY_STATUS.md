# UAA-P1-066 Local Model Manager Read-Only Control Center Inventory/Status

Status: Ready Next
Baseline: v0.102.3
Parent lane: M170 Local Model Product Loop
Predecessor: UAA-P1-065 Founder Command Center Review/Cleanup Lane
Source implementation: UAA-P1-064 Local Model Inventory Read-Only Backend + CLI
Decision date: 2026-06-21

## Purpose

UAA-P1-066 is the Ready Next Local Model Manager continuation milestone after
the completed Founder Command Center board cleanup. It promotes a strictly
read-only Control Center model inventory and status surface over the Python
Agent Core inventory introduced by UAA-P1-064.

The milestone keeps Python Agent Core as the source of local model truth.
Control Center may render backend-owned inventory/status state, but it must not
own model truth in React state and must not expose lifecycle, switch, activate,
download, adapter, or settings mutation authority.

## Scope

- Define and, when implemented under this exact milestone, expose a read-only
  Control Center model inventory/status surface backed by UAA-P1-064 inventory
  data.
- Show safe model refs, runtime family, artifact kind, source class, role
  hints, size bucket, runnable status, blocked reason code, memory posture
  bucket, adapter requirement, inventory summary state, and explicit
  unavailable/blocked states.
- Preserve CLI parity through `uaa local-model status`, `uaa local-model list`,
  and `uaa local-model inspect <model-ref>` as the inspection path.
- If a backend route is required, it must be read-only, side-effect classified,
  covered by OpenAPI/API manifest tests, and backed by Python Agent Core state.
- If no backend route is added, the milestone must remain docs/planning only and
  must not create a React-owned source of truth.
- Add focused frontend/docs/tests only for read-only display and blocked-state
  language.

## Required UI Posture

- The Models surface must distinguish `runnable_now`, `needs_adapter`,
  `blocked`, missing roots, unknown inventory, and stale/unavailable states.
- The UI must display safe refs and human-readable state first, not raw JSON as
  the primary operator view.
- The UI must name missing authority for lifecycle, switching, activation,
  downloads, runtime adapters, and identity updates.
- The UI must not imply a model is loaded, running, switched, activated, or
  identity-updated without backend receipt/evidence refs from a later scoped
  milestone.

## Non-Goals

- No start, stop, activate, switch, unload, or lifecycle controls.
- No Desktop/Hermes activation control.
- No `llama-server` process control or router-mode wiring.
- No dry-run switch planner and no executable switch.
- No model downloads, model movement, search/acquisition, or adapter execution.
- No MLX, Ollama, or LM Studio runtime adapter start.
- No model/provider calls, web fetching, browser automation, plugin runtime
  import, connector writes, shell/subprocess execution, remote execution, or
  public distribution authority.
- No React-owned model truth, no raw local path evidence, and no production
  readiness claim.

## Verification Commands

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_uaa_p1_064_local_model_inventory.py tests/test_dev_launcher.py
.venv/bin/python scripts/verify_uaa_p1_064_local_model_inventory_scope.py
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_product_truth.py --root .
git diff --check
```

If this milestone later adds a Control Center implementation, also run:

```bash
make frontend-check
.venv/bin/python scripts/verify_control_center_frontend.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
```

Run OpenAPI/API manifest checks only when the implementation adds or changes a
route contract.

## Stop And Ask Conditions

Pause before implementation if the work appears to require lifecycle control,
model switching, activation, downloads, runtime adapters, process control,
model calls, route authority beyond read-only status, raw local paths, or any
claim that a local model is loaded, running, switched, activated, or safe to use
without later backend receipts.
