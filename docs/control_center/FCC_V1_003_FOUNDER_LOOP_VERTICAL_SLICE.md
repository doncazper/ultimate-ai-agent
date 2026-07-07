# FCC-V1-003 Founder Loop V1 Vertical Slice

Status: implemented for the first receipt-bearing vertical slice.

Contract ref: `contract-ref:founder-loop-v1-vertical-slice:v1`.

FCC-V1-003 makes one local Founder Loop path real:

```text
Today item -> Action envelope -> exact approval/edit/reject/defer receipt -> Evidence Timeline
```

This is not an action-execution milestone. It does not execute the approved
action, grant connector writes, call providers or models, run shell/subprocess
work, write memory, inject context, enable public beta, or grant production
authority.

## Implemented Scope

- `POST /control-center/today/action-envelope` creates a reviewable Action
  envelope from a safe Today item ref.
- The route is protected, `mutating_requires_authority`,
  `local_dev_workspace_only`, active `workspace/draft` AuthorityLease-gated,
  idempotency-gated, and rate-limited under `today_to_action_envelope`.
- The created envelope carries exact scope refs, risk class, side-effect class,
  approval requirement refs, expected receipt refs, idempotency refs, rollback
  refs, safe-disable refs, blocked-state refs, authority decision refs,
  authority lease refs, and safe evidence refs.
- Same idempotency key plus same payload returns the prior promotion receipt.
- Same idempotency key plus conflicting payload is rejected.
- Action approve/edit/reject/defer decisions continue through the FCC-V1-002
  backend state machine and produce durable receipts.
- Approve validates an exact `LocalApprovalAuthority` grant before the receipt
  can become `approved`.
- Edit, reject, and defer produce receipts without execution.
- Today summary Evidence Timeline entries show what was proposed, what was
  approved or decided, what happened, what changed, what can be undone, and
  what remains blocked through safe refs.
- `scripts/dev/uaa_founder_loop.py` provides the repo-local inspection and
  promotion path outside React.

## Evidence And Receipts

Implemented proof refs:

- `scripts/verify_fcc_v1_003_founder_loop_vertical_slice.py`
- `tests/test_fcc_v1_003_founder_loop_vertical_slice.py`
- `scripts/dev/uaa_founder_loop.py`
- `apps/control-center/src/components/FounderLoopPanels.tsx`
- `apps/control-center/src/App.test.tsx`

The verifier exercises the full local path in a temporary Founder Loop state
store:

- missing idempotency is rejected;
- first Today-to-Action promotion creates a durable receipt with authority
  decision refs;
- duplicate matching promotion replays the prior receipt;
- conflicting duplicate promotion is rejected;
- CLI inspect and promote commands return safe refs with raw paths omitted;
- exact approval uses `LocalApprovalAuthority`;
- edit, reject, and defer each produce receipts;
- Evidence Timeline state contains the promoted action history.

## Authority Boundary

All receipts preserve denied authority flags. Approval refs remain identifiers
until exact `LocalApprovalAuthority` validation succeeds, and even an approved
decision remains decision-state only. Today-to-Action promotion requires active
`workspace/draft` AuthorityLease scope before local review-only state is
written. Execution, connector writes,
shell/subprocess work, provider/model calls, memory writes, context injection,
rollback execution, public distribution, and production authority remain
blocked.

## Remaining Work

FCC-V1-004 must add durable Chat receipts and handoff refs. FCC-V1-005 must
add Memory Review accept/correct/reject backend decisions. FCC-V1-006 must
productize richer Evidence Timeline events. FCC-V1-007 owns proof-lane
promotion rules before any visible route can move beyond conservative
`partial` release status.
