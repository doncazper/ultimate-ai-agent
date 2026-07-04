# Phase 03: Local Model Runtime Gateway

Goal: implement real local model calls through one governed runtime gateway.

This phase promotes model runtime authority only for configured loopback/local
OpenAI-compatible endpoints. Do not add remote provider SDK calls or broad
provider authority.

## Required Work

1. Implement `LocalModelRuntimeAdapter` behind `RuntimeGateway`.
2. Allow only configured loopback/local endpoints by default, such as
   `127.0.0.1`, `localhost`, or an explicitly approved local socket.
3. Require runtime profile `local-runtime` or stronger.
4. Treat model output as untrusted proposal text.
5. Produce a runtime invocation receipt for every call attempt.
6. Store redacted metadata only:
   - adapter id;
   - model ref or safe model alias;
   - timestamp;
   - profile;
   - policy decision;
   - request/response byte counts;
   - bounded redacted preview only if allowed;
   - error category without raw payload echo.
7. Integrate Chat so it can use the runtime gateway when enabled and return a
   clear blocked/disabled state when not enabled.

## Hard Blocks

- No raw prompt persistence.
- No raw response persistence.
- No provider payload persistence.
- No remote provider SDK.
- No ambient environment credential loading unless a scoped secret-store
  contract already exists and is tested.
- No tool calls from model output in this phase.
- No model output as production authority.

## Acceptance Criteria

- Disabled-by-default behavior is tested.
- Loopback/local allowlist is tested.
- Non-loopback URL is blocked and redacted.
- Model-down and timeout failures produce safe receipts.
- Chat route/UI copy distinguishes local model runtime from production
  authority.
- Manifest truth says local model pilot is implemented and remote provider
  authority remains blocked.

## Verification

Run focused model runtime tests plus:

```bash
git diff --check
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
```
