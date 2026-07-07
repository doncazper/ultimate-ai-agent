# UAA Hermes Runtime Checkpoint Rollback

Status: Hermes Runtime Adoption Phase 18 AuthorityState-bound repo-safe read model

## Full-Strength Version

Every UAA mutation lane checkpoints before change and can roll back by proof ref
through an exact approved lane with idempotency, receipts, redaction, and
operator-visible proof.

## Repo-Safe Version

Phase 18 adds Python Core checkpoint/rollback posture for exact and future
mutation lanes:

- `GET /api/runtime/checkpoint-rollback`
- `scripts/dev/uaa_runtime.py inspect-checkpoint-rollback`
- `RuntimeCheckpointRollbackReadModel`
- exact lane checkpoint refs, checkpoint hash refs, mutation receipt refs,
  rollback-plan refs, rollback receipt refs, approval scope refs, idempotency
  refs, AuthorityState route/CLI/mapping/catalog/decision/reason refs,
  unsupported adapter refs, proof refs, verifier refs, and blocked authority
  refs

Current lane posture covers file patch core rollback receipts, Work Board
reorder receipt posture, CRM local mutation receipt posture, local task commit
rollback readiness, and blocked Coding patch apply readiness.

The read model is mapped as `lane-ref:runtime-checkpoint-rollback-read-model`
under Read-only `workspace/read` and is evaluated from the active
AuthorityLease decision catalog. This is read-only posture only. It does not
create checkpoints, execute rollback, take broad filesystem snapshots, mutate
Git, persist raw content or raw paths, call providers/models, run
shell/subprocess commands, automate browsers, or claim production authority.

## Blocked / Needs Authority

- broad filesystem snapshots
- rollback execution routes
- Git mutation or Git-backed rollback
- raw checkpoint payload persistence
- raw path or raw content persistence
- rollback without exact LocalApprovalAuthority scope
- production authority

## Exact Promotion Path

Future promotion requires exact workspace scope, checkpoint hash, mutation
receipt, rollback receipt, idempotency, approval scope validation, safe-disable
posture, redaction, CLI/API/Core parity, route classification updates, and
focused verifier coverage. Rollback approval must bind to the exact rollback
plan and cannot become a broad undo switch.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_hermes_runtime_checkpoint_rollback.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_18.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
```
