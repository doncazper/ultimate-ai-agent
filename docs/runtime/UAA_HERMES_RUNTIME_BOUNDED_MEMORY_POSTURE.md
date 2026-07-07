# UAA Hermes Runtime Bounded Memory Posture

Status: implemented as backend-owned read/review posture for Hermes Runtime
Adoption Phase 11.

UAA now exposes a bounded governed memory posture inside the existing Memory
Workbench and Memory Review read models. The posture is owned by Python Agent
Core and rendered by Control Center as operator-facing product truth.

## Full-Strength Intent

UAA should support compact durable user, profile, and project memory with
operator review, quality controls, correction/rejection posture, provenance,
staleness handling, target selection, and proof-linked impact review.

## Repo-Safe Phase 11 Scope

Phase 11 adds `contract-ref:hermes-runtime-adoption-bounded-memory-posture:v1`
as a safe-ref-only posture embedded in:

- `GET /control-center/memory/workbench`
- `GET /control-center/memory/review`
- `scripts/dev/uaa_founder_loop.py memory-bounded-posture`
- Control Center Memory Review

The read model includes:

- capacity posture: visible item count, candidate count, context-pack count,
  ref caps, token estimate, and search index posture
- target posture: user/profile/project target kinds, target refs, and
  operator-selected context requirement
- source posture: source refs, provenance refs, evidence refs, receipt refs,
  and safe-summary-only guarantees
- staleness posture: stale counts, stale refs, and recheck-before-recall state
- why-shown posture: why-shown refs, included reason refs, and quality refs
- quality review posture: review-before-recall, correction/rejection support,
  receipt refs, exact reviewed-recall write scope, and rollback/supersede
  posture
- context-pack posture: proposal refs only, no prompt context write, and no
  context injection authority

## Blocked Authority

The posture does not grant:

- autonomous memory writes
- automatic memory writes
- hidden prompt or context injection
- external memory provider writes
- semantic provider calls, embeddings, or vector DB authority
- model/provider calls
- live web fetches
- connector writes
- delete/export execution
- background autonomy
- production authority

Memory remains recall and review posture, not truth or action authority.

## AuthorityLease Capability Path

Any future memory write, injection, external memory provider, or delete/export
capability must prove exact scope, LocalApprovalAuthority binding, idempotency,
receipt/proof refs, rollback or supersede posture, safe-disable behavior,
redaction, CLI/API/Core parity, route classification, and focused verifier
coverage before it can become active AuthorityLease scope.

## Verification

Focused verification:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_11.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_fcc_mem_001_memory_workbench.py tests/test_fcc_v1_005_memory_review_decisions.py -q
```
