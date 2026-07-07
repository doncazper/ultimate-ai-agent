# UAA Hermes Runtime Doctor Diagnostics

Status: Hermes Runtime Adoption Phase 28, AuthorityState-bound repo-safe read model.

## Full-Strength

One UAA diagnostic command explains setup, runtime readiness, providers, tools,
protected material posture, local services, authority, and next safe actions
without making the operator hunt across panels.

## Repo-Safe

Phase 28 adds Python Core ownership for redacted local diagnostic posture:

- `RuntimeDoctorDiagnosticsReadModel`
- `GET /api/runtime/doctor-diagnostics`
- `scripts/dev/uaa_runtime.py inspect-doctor-diagnostics`
- Authority mapping `lane-ref:runtime-doctor-diagnostics-read-model` as
  Read-only `workspace/read`
- Control Center `/runtime` doctor diagnostics card

The read model exposes diagnostic refs, source route refs, CLI refs, proof refs,
blocked authority refs, next-safe-action refs, AuthorityState route/CLI/mapping/
catalog/decision/reason refs, unsupported adapter refs, and decision-bound
snapshot hashes. It stores safe refs and bounded summaries only.

## Blocked / Needs Authority

- Installs.
- Service starts or restarts.
- Credential writes.
- Runtime config mutation.
- Provider payload persistence.
- Raw log or raw local path persistence.
- Control Center minting authority.

## Exact Promotion Path

1. Add setup action proposal contracts.
2. Bind each proposed action to an approval envelope.
3. Require idempotent receipts for any local mutation.
4. Add rollback or safe-disable proof for each action type.
5. Link diagnostic actions to Proof Detail.
6. Add focused tests for redaction, route classification, approval binding,
   receipt creation, rollback posture, and product-language boundaries.

## Verification

- `tests/test_hermes_runtime_doctor_diagnostics.py`
- `scripts/verify_hermes_runtime_adoption_phase_28.py`
