# Phase 02: Runtime Contracts, Profiles, Storage, And Manifest

Goal: add the governed runtime contract layer before adding adapters.

This phase defines schemas, profiles, route contracts, storage, and manifest
truth. It may add dry-run/status endpoints, but it must not perform model calls
or command execution yet.

## Required Concepts

Create or extend core contracts for:

- `RuntimeAuthority`
- `RuntimeProfile`
- `RuntimeInvocationRequest`
- `RuntimePolicyDecision`
- `RuntimeApprovalRequirement`
- `RuntimeInvocationReceipt`
- `RuntimeArtifactRef`
- `RuntimeRollbackRef`
- `RuntimeSafeDisableState`

Profiles:

- `sealed`: default. No runtime model/tool execution.
- `local-runtime`: local model and allowlisted command adapters may be enabled
  by config.
- `operator-approved`: execution requires exact approval envelope before the
  adapter runs.

## API Shape

Add typed route contracts for:

```text
GET  /api/runtime/capabilities
GET  /api/runtime/invocations
POST /api/runtime/invocations
GET  /api/runtime/invocations/{id}
GET  /api/runtime/invocations/{id}/receipt
POST /api/runtime/invocations/{id}/approve
POST /api/runtime/invocations/{id}/execute
POST /api/runtime/safe-disable
```

Routes may initially return blocked, disabled, pending approval, or dry-run
states. They must be classified in OpenAPI and `/api/manifest`.

## Storage Shape

Add durable storage for:

- runtime invocation metadata;
- runtime policy decisions;
- approval bindings;
- receipt refs;
- redacted artifact refs;
- replay/idempotency state;
- safe-disable state.

Do not store raw prompts, raw responses, raw command output, raw local paths,
provider payloads, full env dumps, credentials, or secret-like values.

## Acceptance Criteria

- Runtime profiles are explicit and default to `sealed`.
- Route side-effect classifications are correct.
- Mutating routes require idempotency where appropriate.
- Auth posture is explicit.
- Manifest/OpenAPI tests cover every new route.
- Storage tests prove redacted/safe-ref persistence.
- No adapter can execute in this phase.

## Verification

Run:

```bash
git diff --check
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
```

Add focused runtime contract/storage tests.

