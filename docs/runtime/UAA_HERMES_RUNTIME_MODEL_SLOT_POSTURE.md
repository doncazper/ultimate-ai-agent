# UAA Hermes Runtime Model Slot Posture

Status: Hermes Runtime Adoption Phase 08 repo-safe read model.

UAA now exposes main and auxiliary model slot intent through the backend-owned
model/provider control plane. This is UAA-native routing posture, not hidden
model routing and not provider/model invocation authority.

## Implemented

- `ModelProviderControlPlaneReadModel.model_slot_posture`.
- `GET /control-center/providers/runtime-control-plane`.
- `scripts/inspect_model_provider_control_plane.py`.
- `scripts/verify_hermes_runtime_adoption_phase_08.py`.
- Control Center Models card for main and auxiliary model slots.
- Trust lane `trust-lane:model-slot-posture`.

The read model lists slots for main thinking, summarization, title generation,
approval scoring, compression, retrieval, vision, and review. Each slot records
intended provider/model refs, readiness posture, route-decision trace refs,
cost/latency posture, warning refs, model-output truth refs, and blocked
authority refs.

## Repo-Safe Behavior

- Shows intended model-slot refs and warnings only.
- Keeps runtime-reported availability separate from UAA invocation authority.
- Requires future route-decision traces, cost estimates, approval/profile
  mapping, model-output truth envelopes, and receipts before any execution.
- Keeps raw prompts, raw responses, and provider payloads out of durable state.

## Blocked

- Live auxiliary model calls.
- Provider SDK use.
- Runtime selection or default-model mutation.
- Hidden model routing.
- Approval decisions delegated to a model.
- Raw prompt or response persistence.
- Model output as product truth or action authority.

## Promotion Path

Any future model-slot execution lane needs exact slot, provider, model,
profile, credential, cost, route-decision, approval, idempotency, receipt,
truth-envelope, safe-disable, rollback, CLI/API/Core parity, route
classification, and focused verifier coverage.
