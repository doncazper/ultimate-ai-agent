# UAA-P1-064 Local Model Inventory Read-Only Backend + CLI

Status: Implemented
Baseline: v0.103.0
Parent lane: M170 Local Model Manager
Predecessor: UAA-P1-062 Local Model Manager Shape
Decision date: 2026-06-21

## Purpose

UAA-P1-064 is the first implementation milestone for the governed local model
manager lane. It turns the UAA-P1-062 shape into a read-only inventory surface
that safely describes local model candidates before any lifecycle, switching,
or Control Center activation work exists.

The milestone keeps Python Agent Core as the authority. The CLI is the first
operator surface. Any later Control Center model UI must call the same core/API
contract and must not own model truth in React state.

## Scope

- Build a read-only Python Agent Core inventory over operator-configured local
  model roots. The core inventory has no implicit home-directory scan; operators
  must pass explicit roots through CLI `--root` values or `UAA_LOCAL_MODEL_ROOTS`.
- Detect local model candidates from GGUF, Hugging Face/MLX-style directories,
  Ollama manifests or blobs, LM Studio-style directories, and MLX directories
  without opening model weights or making runtime model calls.
- Return only safe model references and redacted summaries: model ref, runtime
  family, artifact kind, source class, role hints, size bucket, runnable status,
  blocked reason code, memory posture bucket, and adapter requirement.
- Add CLI parity first:
  - `uaa local-model status`
  - `uaa local-model list`
  - `uaa local-model inspect <model-ref>`
- Treat runnable status as descriptive only:
  - `runnable_now`
  - `needs_adapter`
  - `blocked`
- Add focused tests and a documentation verifier that prove the milestone stays
  read-only, redacted, and aligned with the UAA-P1-062 roadmap.

## Required Inventory Behavior

- Stable model refs must avoid raw local paths and must be deterministic across
  repeated inventory runs when the same model candidate is present.
- The inventory must not expose raw prompts, raw responses, provider payloads,
  raw local paths, raw logs, usernames, hostnames, serials, environment dumps,
  credential material, or secret-like values in durable evidence.
- Missing directories, unreadable metadata, unsupported quantizations, and
  missing runtime adapters must become explicit blocked or needs-adapter states
  rather than exceptions in normal operator flows.
- Filesystem inspection must be bounded and metadata-first. Weight files can be
  counted or size-bucketed, but not parsed as model authority.
- CLI output must be structured enough for operator inspection and testable
  without relying on Control Center UI state.

## Non-Goals

- No start, stop, activate, switch, or unload behavior.
- No process control and no llama.cpp lifecycle management.
- No `llama-server --models-dir` router mode wiring.
- No dry-run switch planner and no approval-bound real switch.
- No Control Center activation control.
- No model downloads or model movement.
- No provider SDK calls, model calls, web fetching, browser automation, plugin
  runtime import, connector writes, or remote execution.
- No OpenAPI or route authority unless a later exact scoped milestone explicitly
  grants it with tests and side-effect classification.
- No MLX, Ollama, or LM Studio runtime adapter execution.
- No production-readiness, public distribution, or broad autonomy claims.

## Implementation Evidence

- `docs/model_management/UAA_P1_064_LOCAL_MODEL_INVENTORY_READ_ONLY.md` defines
  the read-only scope, non-goals, CLI parity, and evidence requirements.
- `src/ultimate_ai_agent/core/local_model_management/inventory.py` implements
  bounded, metadata-first, read-only inventory with safe model refs and no raw
  local path output.
- `scripts/dev/uaa_local_model.py` and `scripts/dev/uaa_launcher.py` expose CLI
  parity for `uaa local-model status`, `uaa local-model list`, and
  `uaa local-model inspect <model-ref>`.
- `tests/test_uaa_p1_064_local_model_inventory.py`,
  `tests/test_dev_launcher.py`, and
  `tests/test_uaa_p1_064_local_model_inventory_scope.py` cover core inventory,
  CLI dispatch, scope, and artifact guardrails.
- `docs/kanban/current_board.md` records UAA-P1-064 as done for read-only
  inventory and CLI inspection only.
- `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md` points M170 from the
  UAA-P1-062 shape to UAA-P1-064 as the completed first implementation slice.
- `docs/backlog/reconciliation/2026-06-21-uaa-p1-064-ready-next-promotion.json`
  records this implementation pass with safe evidence refs and keeps runtime
  authority blocked.
- A focused verifier and tests bind the scope and stop conditions.

## Verification Commands

```bash
.venv/bin/python scripts/verify_uaa_p1_064_local_model_inventory_scope.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_uaa_p1_064_local_model_inventory.py tests/test_uaa_p1_064_local_model_inventory_scope.py tests/test_dev_launcher.py
.venv/bin/python scripts/verify_documentation_integrity.py
git diff --check
```

## Stop And Ask Conditions

Pause before implementation if the work appears to require lifecycle control,
downloads, model execution, new dependencies, OpenAPI/route changes, Control
Center controls, raw-path evidence, or any authority beyond read-only inventory
and CLI inspection.
