# Phase 06: Role-Based Model And Provider Evidence

Goal: improve UAA's model/provider routing score without granting new model
runtime authority. UAA should show role-based provider readiness, constraints,
and selection evidence even when actual invocation remains blocked.

Reference pattern: GoatCitadel ranks provider/model choices per orchestration
role with evidence and candidate scoring. Borrow the evidence shape, not the
runtime authority.

## Required Work

1. Inspect UAA's model router, provider profiles, local runtime manifests,
   runtime readiness, cost/latency metadata, and Control Center settings.
2. Define or harden role profiles such as:
   - answerer;
   - planner;
   - reviewer;
   - synthesizer;
   - coder;
   - extractor;
   - safety reviewer.
3. Build a UAA-native selection evidence object that includes:
   - role ref;
   - candidate provider/model refs;
   - capability scores or readiness labels;
   - cost/latency visibility when known from config or profile;
   - local/remote authority status;
   - disabled/blocked reason;
   - policy decision ref;
   - fallback ref;
   - redacted evidence ref.
4. Ensure remote providers remain blocked unless a separate accepted milestone
   grants exact authority.
5. Connect selection evidence to route decisions or orchestration plans as
   advisory metadata, not execution authority.
6. Add CLI/API/Control Center inspection where appropriate.
7. Add tests for role ranking, disabled provider handling, remote blocked
   state, fallback evidence, and no invocation.

## Explicit Non-Goals

- Do not call a model.
- Do not add provider SDK dependencies.
- Do not load ambient credentials.
- Do not treat provider selection as permission to execute.

## Acceptance Criteria

- Model/provider routing becomes evidence-rich and operator-visible.
- The UI/CLI can explain why a model/provider is selected, blocked, or
  fallback-only.
- Tests prove no invocation and no authority broadening.
- Product language distinguishes readiness evidence from runtime authority.

## Verification

Run focused model-router/runtime-readiness tests plus:

```bash
git diff --check
PYTHONPATH=src .venv/bin/python -m pytest tests/test_model_runtime_no_real_calls.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_capability_matrix.py -q
```
