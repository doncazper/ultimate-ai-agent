# UAA Hermes Runtime Fail-Closed Approval Timeouts

Status: Hermes Runtime Adoption Phase 26, repo-safe hardening.

## Full-Strength

All delegated runtime approval waits deny by default when expired, ambiguous,
stale, scope-mismatched, or missing a current UAA approval envelope. Runtime
approval is never inferred from a ref alone.

## Repo-Safe

Phase 26 hardens the existing Python Core approval bridge and exact approved
command lane:

- `RuntimeApprovalBridgeReadModel.fail_closed_timeout_posture` exposes the
  fail-closed timeout policy, denial receipt refs, blocked broad authority refs,
  promotion path refs, and next safe action refs.
- `GET /api/runtime/approval-bridge` and
  `scripts/dev/uaa_runtime.py inspect-approval-bridge` return the same posture.
- Control Center `/runtime` displays timeout, ambiguous wait, approve-all,
  standing authority, and expired-grant posture as read-only backend-owned
  state.
- Expired Action Inbox approval execution attempts fail closed with
  `RUNTIME_COMMAND_ACTION_INBOX_APPROVAL_EXPIRED`, a blocked receipt, and no
  runner invocation.

## Blocked / Needs Authority

- Auto-approve.
- Approve-all.
- Standing broad authority.
- Reuse of expired grants.
- Ambiguous approval waits as authority.
- Sending approval, denial, or timeout resolutions to delegated runtimes from
  this read-model lane.

## Exact Promotion Path

1. Define a narrow session-scoped grant with explicit expiration.
2. Validate exact `LocalApprovalAuthority` scope before any runtime resolution.
3. Bind a denial or timeout receipt to the run, Action Inbox item, proof ref,
   idempotency ref, safe-disable posture, and revoke path.
4. Prove stale, expired, ambiguous, and scope-mismatched waits deny by default.
5. Add CLI/API/Core/Control Center parity, route side-effect classification,
   redaction tests, replay tests, and rollback/safe-disable evidence.

## Verification

- `tests/test_hermes_runtime_approval_bridge.py`
- `tests/test_governed_runtime_contracts.py`
- `scripts/verify_hermes_runtime_adoption_phase_26.py`
