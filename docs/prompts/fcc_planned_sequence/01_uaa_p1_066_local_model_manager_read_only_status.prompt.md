# UAA-P1-066 Local Model Manager Read-Only Control Center Inventory/Status

Role: You are a Principal Software Engineer implementing or repairing the
Ready Next Local Model Manager support lane.

Task: Make UAA-P1-066 true in the current repository: a strictly read-only
Control Center model inventory/status surface backed by the UAA-P1-064 Python
Agent Core inventory and CLI inspection contract.

Read first:
- `AGENTS.md`
- `docs/model_management/UAA_P1_066_LOCAL_MODEL_CONTROL_CENTER_READ_ONLY_STATUS.md`
- `docs/model_management/UAA_P1_064_LOCAL_MODEL_INVENTORY_READ_ONLY.md`
- `docs/kanban/current_board.md`
- `docs/kanban/founder_command_center_board.md`
- `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`
- `docs/control_center/operational_maturity_manifest.json`
- `src/ultimate_ai_agent/core/local_model_management/inventory.py`
- existing Control Center Models route/API/frontend/tests

Requirements:
- Python Agent Core remains the source of local model inventory truth.
- Expose or verify backend-owned read-only status over safe model refs,
  runtime family, artifact kind, source class, role hints, size bucket,
  runnable status, blocked reason code, memory posture bucket, adapter
  requirement, inventory summary state, unavailable/blocked states, and gateway
  posture.
- Preserve CLI parity through `uaa local-model status`, `uaa local-model list`,
  and `uaa local-model inspect <model-ref>`.
- If a route exists, ensure it is read-only, protected consistently with local
  Control Center routes, side-effect classified, OpenAPI/API-manifest visible,
  and tested.
- If no route exists, keep the milestone docs-only and do not create
  React-owned model truth.
- Keep product/docs truth aligned: implemented, partial, planned, blocked, and
  intentionally out of scope must stay distinct.

Non-goals:
- No start, stop, activate, switch, unload, lifecycle control, Desktop/Hermes
  activation, downloads, runtime adapters, process control, model movement,
  search/acquisition, settings apply, provider/model calls, web fetching,
  browser automation, connector writes, shell/subprocess execution, plugin
  runtime import, remote execution, raw local path evidence, or production
  readiness claim.

Focused checks:
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_uaa_p1_064_local_model_inventory.py tests/test_control_center_api_routes.py tests/test_api_manifest.py -q`
- `.venv/bin/python scripts/verify_uaa_p1_064_local_model_inventory_scope.py`
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `.venv/bin/python scripts/verify_product_truth.py --root .`
- `make frontend-check` if frontend files changed
- `git diff --check`

Output:
- UAA-P1-066 decision: implemented, implemented with conditions, or blocked.
- Evidence proving the decision.
- Files changed.
- Tests/verifiers run.
- Behavior explicitly not added.
