# FCC-V1-002 Action Inbox Backend State Machine

Status: implemented for backend-owned Action Inbox decision state.

FCC-V1-002 makes Action Inbox approve, edit, reject, defer, and cancel decisions
backend-owned, atomic, idempotent, revision-bound, receipt-backed, and gated by active
`workspace/write` AuthorityLease scope. It does not execute the approved action
and does not grant connector, shell/subprocess, provider/model, memory-write,
public beta, distribution, or production authority.

## Implemented Boundary

- Core contracts: `contract-ref:founder-loop-action-state-machine:v1` and
  `contract-ref:founder-loop-action-revision-lifecycle:v1`.
- Decision statuses: `approved`, `approval_required`, `edited`, `rejected`,
  `deferred`, `cancelled`, `blocked`, and `replayed`.
- Decision routes:
  - `POST /control-center/actions/{action_id}/approve`
  - `POST /control-center/actions/{action_id}/cancel`
  - `POST /control-center/actions/{action_id}/edit`
  - `POST /control-center/actions/{action_id}/reject`
  - `POST /control-center/actions/{action_id}/defer`
  - `GET /control-center/actions/{action_id}/receipt`
- Existing inbox route: `GET /control-center/actions/inbox`.
- Every decision requires the exact current `expected_revision_ref`. Stale
  revisions return a typed HTTP 409 `FOUNDER_LOOP_ACTION_STALE_REVISION` response
  with safe current refs and require an authoritative inbox refresh before intent
  may be retried.
- Approve validates exact `LocalApprovalAuthority` scope when approval is
  required. Approval refs remain identifiers until exact actor, action,
  resource refs, risk, expiry, and classification are validated.
- Approval scope binds the current revision, generation, payload fingerprint,
  decision route, Python Core adapter, authoritative action expiry through its
  deadline ref, and authority-input refs. Changing the expiry invalidates the
  revision and any approval minted for the earlier deadline.
- Approve/edit/reject/defer/cancel decision receipt mutation requires active
  `workspace/write` AuthorityLease scope. Missing or mismatched authority
  records a blocked receipt with authority decision refs and does not mint
  backend-owned approval.
- Edit records a corrected envelope ref only and advances the authoritative
  generation. Edit and cancel atomically invalidate every earlier approval.
  Cancel is idempotent and never executes the action.
- The Control Center enables cancel only for backend-persisted items marked
  `action_revision_decision_eligible`; proposal-only generated rows remain
  visibly non-mutating.
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
- `expected_revision_ref`
- `generation_ref`
- `revision_ref`
- `revision_fingerprint_ref`
- `result_generation_ref`
- `result_revision_ref`
- `approval_scope_ref`
- `decision_route_binding_ref`
- `decision_adapter_ref`
- `decision_deadline_ref`
- `authority_input_refs`
- `invalidated_approval_refs`
- `approval_ref`
- `approval_validated`
- `action_executed`
- `connector_write_performed`
- `memory_write_performed`
- `idempotency_key_ref`
- `audit_ref`
- `evidence_refs`
- `blocked_state_refs`
- `authority_decision_ref`
- `authority_decision_outcome`
- `authority_lease_ref`
- `authority_reason_refs`
- `replayed`

The denied flags remain false for execution, connector writes, memory writes,
provider/model calls, and shell/subprocess work.

## Control Center Surface

The Action Inbox surface binds decisions to the rendered revision and displays
receipt/audit refs. Stale conflicts trigger an authoritative refresh. Refresh
failure preserves the last confirmed UI snapshot and never marks unconfirmed
decision state as committed.

## Remaining Blockers

- Broader Today-to-action execution beyond review-only envelope creation.
- Action execution contract.
- Evidence Timeline mutation binding for action decisions.
- Product `ship`, public beta, public distribution, and production authority
  claims.

## Verification

```bash
.venv/bin/python scripts/verify_fcc_v1_002_action_inbox_state_machine.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_fcc_v1_002_action_inbox_state_machine.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_founder_loop_api.py tests/test_control_center_founder_loop_api_manifest.py tests/test_founder_loop_storage.py
npm --prefix apps/control-center run test -- --run App.test.tsx
```
