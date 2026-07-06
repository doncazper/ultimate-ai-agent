# UAA Hermes Runtime Model Provider Catalog

Status: Hermes Runtime Adoption Phase 07 repo-safe read model.

UAA now folds delegated runtime model availability into the backend-owned
model/provider control plane. This is a UAA-native catalog posture, not a
Hermes import and not provider execution authority.

## Implemented

- `ModelProviderControlPlaneReadModel.delegated_runtime_model_catalog`.
- `GET /control-center/providers/runtime-control-plane`.
- `scripts/inspect_model_provider_control_plane.py`.
- `scripts/verify_hermes_runtime_adoption_phase_07.py`.
- Control Center Models surface card for delegated runtime model availability.

The catalog separates runtime-reported availability from UAA invocation
authority. Runtime rows can say a delegated runtime reports or plans a model
ref, while UAA still records `uaa_invocation_allowed: false` and
`uaa_authorized_model_count: 0`.

## Repo-Safe Behavior

- Shows UAA-owned profile refs separately from delegated runtime profile refs.
- Shows model refs, source refs, static cost posture, and latency posture.
- Shows local llama.cpp metadata as catalog visibility only.
- Keeps provider SDK calls, remote model calls, live provider discovery,
  credential collection, billing authority, model-output authority, and raw
  provider payload persistence blocked.

## Blocked

- Provider credential collection or OAuth.
- Provider SDK calls.
- Remote model invocation.
- Live provider/model discovery.
- Billing actions or spend authority.
- Runtime default/model selection mutation.
- Model output as product truth or action authority.

## Promotion Path

Any future invocation lane needs exact provider/model/profile refs, credential
ref binding, CostGovernor decision refs, approval binding, idempotency,
redacted receipts, safe-disable posture, CLI/API/Core parity, route
classification review, and focused verifier coverage.
