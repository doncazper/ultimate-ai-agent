# Phase 05: Action Inbox Execution Bridge

Goal: connect Action Inbox approvals to real governed runtime execution.

This phase makes Action Inbox useful: an exact approved envelope can execute a
pending runtime invocation through `RuntimeGateway`.

## Required Work

1. Extend Action Inbox item/envelope types to represent runtime invocation
   approvals.
2. Bind each approval to:
   - runtime invocation id;
   - adapter id;
   - command/model intent;
   - exact scope;
   - risk class;
   - expiration;
   - policy decision;
   - idempotency key;
   - rollback/safe-disable posture.
3. Implement approve/deny/expire/replay states for runtime action envelopes.
4. Ensure approve does not execute if:
   - scope changed;
   - runtime profile changed to weaker/disabled;
   - safe-disable is active;
   - policy decision is stale or denied;
   - approval expired;
   - invocation already completed with conflicting idempotency payload.
5. Execute through the runtime gateway only after exact validation.
6. Store approval and execution receipts.

## UX Contract

The operator must see:

- what will run;
- why it needs approval;
- what data can be touched;
- what evidence will be stored;
- what remains blocked;
- how to deny or safe-disable.

No raw JSON should be the primary operator-critical UX.

## Acceptance Criteria

- Approval refs cannot authorize any changed scope.
- Deny and expire paths are tested.
- Replay/idempotency conflict is tested.
- Safe-disable blocks execution after approval.
- Receipt links appear in Action Inbox, Evidence, and CLI.
- Product copy does not claim broad autonomy or production authority.

## Verification

Run focused Action Inbox/runtime tests plus:

```bash
git diff --check
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
make frontend-check
```
