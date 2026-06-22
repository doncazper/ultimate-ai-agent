# FCC-V1-002 Action Inbox Backend State Machine

Status: implemented for backend-owned Action Inbox decision state.

FCC-V1-002 makes Action Inbox approve, edit, reject, and defer decisions
backend-owned, append-first, idempotent, and receipt-backed. It does not
execute the approved action and does not grant connector, shell/subprocess,
provider/model, memory-write, public beta, distribution, or production
authority.

## Implemented Boundary

- Core contract: `contract-ref:founder-loop-action-state-machine:v1`.
- Decision statuses: `approved`, `approval_required`, `edited`, `rejected`,
  `deferred`, `blocked`, and `replayed`.
- Decision routes:
  - `POST /control-center/actions/{action_id}/approve`
  - `POST /control-center/actions/{action_id}/edit`
  - `POST /control-center/actions/{action_id}/reject`
  - `POST /control-center/actions/{action_id}/defer`
  - `GET /control-center/actions/{action_id}/receipt`
- Existing inbox route: `GET /control-center/actions/inbox`.
- Approve validates exact `LocalApprovalAuthority` scope when approval is
  required. Approval refs remain identifiers until exact actor, action,
  resource refs, risk, expiry, and classification are validated.
- Edit records a corrected envelope ref only. It does not execute work and does
  not grant approval.
- Reject and defer record decision state and receipt refs only.
- Reusing the same idempotency key with the same decision payload returns the
  prior receipt with replay posture.
- Reusing the same idempotency key with a different decision payload is
  rejected as an idempotency conflict.

## Receipt Shape

Receipts use safe refs only:

- `receipt_ref`
- `action_id`
- `action_item_ref`
- `decision_ref`
- `decision`
- `status`
- `approval_ref`
- `approval_validated`
- `action_executed`
- `connector_write_performed`
- `memory_write_performed`
- `idempotency_key_ref`
- `audit_ref`
- `evidence_refs`
- `blocked_state_refs`
- `replayed`

The denied flags remain false for execution, connector writes, memory writes,
provider/model calls, and shell/subprocess work.

## Control Center Surface

The `/actions` surface now calls the backend decision routes and displays
receipt/audit refs. The route remains `partial` in the release surface
manifest because FCC-V1-003 still needs the first full Today item to Action
envelope to exact decision to durable receipt to Evidence Timeline loop.

## Remaining Blockers

- Today-to-action envelope creation.
- Action execution contract.
- Evidence Timeline mutation binding for action decisions.
- CLI/repo-local inspection command for the first full vertical loop.
- Product `ship`, public beta, public distribution, and production authority
  claims.

## Verification

```bash
.venv/bin/python scripts/verify_fcc_v1_002_action_inbox_state_machine.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_fcc_v1_002_action_inbox_state_machine.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_founder_loop_api.py tests/test_control_center_founder_loop_api_manifest.py tests/test_founder_loop_storage.py
npm --prefix apps/control-center run test -- --run App.test.tsx
```
