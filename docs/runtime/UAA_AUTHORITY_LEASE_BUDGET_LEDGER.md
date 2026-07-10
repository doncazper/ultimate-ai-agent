# AuthorityLease Durable Budget Ledger V1

Status: implemented Python Core budget foundation with initial governed
dispatcher consumption; universal adapter and Control Center mutation
integration remain missing

Date: 2026-07-10

## Implemented Boundary

AuthorityLease V1 now supports two typed, integer constraints:

- `operation_budget`: maximum cumulative operation count for one lease;
- `cost_budget_microusd`: maximum cumulative cost in integer micro-USD for one
  lease.

`AuthorityBudgetStore` records reservations, durable start claims, settlements,
releases, and denials in `authority_budget_receipts.jsonl` under
`UAA_AUTHORITY_STATE_DIR`. The ledger
is append-first, fsync-backed, hash-chained, safe-ref-only, and protected by the
same single-writer lock used for AuthorityLease issue and revoke. Lease writes
use an fsync-backed temporary file plus atomic replace. Concurrent store
instances therefore cannot spend the same local lease capacity twice on the
supported macOS/Linux file-lock path.

The budget store never executes an action. It only records whether exact
capacity is reserved or unavailable.

## Reservation Contract

A reservation must bind all of the following:

- an active `AuthorityLease` ref;
- a complete `AuthorityActionRequest` that independently evaluates to `allow`,
  or evaluates to `ask` and carries exact trusted LocalApprovalAuthority
  validation;
- exact operation and estimated-cost claims matching the action's typed
  constraint claims;
- structured cost-estimate and CostGovernor decision refs;
- the full dispatch fingerprint when the central dispatcher is the caller;
- an explicit CostGovernor allowed posture;
- an idempotency ref and bounded safe summary.

The store re-reads active leases while holding the authority-state lock and
rechecks policy outcome, lease identity, typed budget constraints, cumulative
usage, unresolved actual cost, revocation/expiry, and the local kill switch.
Missing budgets, unknown estimated cost, CostGovernor denial, claim drift,
policy denial, exhausted capacity, or stale lease binding produces a durable
denial receipt and no reservation.

CostGovernor refs are a required integration contract, not self-sufficient
proof of a CostGovernor evaluation. The initial central dispatcher supplies
them from the same typed dispatch request and recomputes CostGovernor from a
typed estimate plus an exact run-scoped budget set for explicitly registered
safe tool adapters. Its dispatch fingerprint binding prevents a reservation
replay after a crash from authorizing changed adapter input. Direct budget-store
callers still need a trusted integration boundary, and paid provider execution
still needs exact live usage and cost proof.

## Settlement And Release

Before the central dispatcher invokes an adapter, the budget ledger moves its
dispatch-bound reservation from `reserved` to `started` with the exact dispatch
fingerprint and execution ref. The transition is idempotent and is written
under the shared authority-state lock before the dispatch-start receipt. A
started reservation continues consuming its reserved capacity and cannot be
released by a standalone caller.

After execution starts, that reservation must be settled with the same
execution ref, actual operation count, actual cost plus its safe ref, execution
status, and evidence refs. The
ledger always records actual overage. A settlement exceeding its reservation or
lease ceiling becomes `settled_overage`; any unreviewed reservation overage
freezes future capacity even when actual usage remains below the lease ceiling.
When actual cost is unknown, the settlement becomes
`settled_cost_unresolved` and all later reservations for that lease fail closed
until a future reviewed remediation contract exists.

A reservation may be released only while its durable state is still
`reserved`; the caller's typed `execution_started=False` assertion is not
sufficient once the ledger records `started`. Release frees unstarted capacity
and records the reason ref. `AuthorityDispatcher` supplies durable pre-start,
budget-start, dispatch-start, and pre-start cancellation receipts for its routed
adapters. Direct budget-store callers and legacy execution paths do not gain
adapter-start proof merely from this integration.

## Replay, Corruption, And Read Surfaces

Every operation fingerprints its full request. Repeating the same idempotency
ref and fingerprint returns a non-persisted `replayed` view; changing operation
or request content raises an idempotency conflict. Full ledger history is
validated on every transaction. Duplicate idempotency or reservation history,
invalid receipt semantics, impossible reservation transitions, follow-up
binding drift, broken previous-hash linkage, or changed entry content fails
closed as ledger corruption.

Approval-binding fields added with dispatcher V1 preserve existing V1 ledger
compatibility: hashes are verified against the exact persisted payload, and a
pre-approval-field reservation fingerprint is accepted only when the current
request carries no approval requirement or approval validation request.

The typed `AuthorityBudgetReadModel` reports per-lease active and reservation-
available and kill-switch posture, limits, allocated and remaining capacity,
active and settled counts, unresolved-cost and unreviewed-overage state,
exhausted state, recent receipts, and total
receipt count. Revoked and expired leases remain visible for audit but are
explicitly unavailable with `reason-ref:authority-budget:lease-inactive`. It is
projected through:

- `GET /api/runtime/authority-state#authority_budget`;
- `scripts/dev/uaa_runtime.py inspect-authority-state --json` at
  `authority_state_read_model.authority_budget`.

These are inspection surfaces only. They do not reserve, settle, release,
execute, approve, or mint authority. When no authority state files exist,
inspection also does not create the authority directory or lock file.

## Verified Acceptance Cases

Focused tests cover:

- exact constraint evaluation and applied constraint refs;
- reserve, replay, settle, overage, release, and cumulative exhaustion;
- exact dispatch start, replay, execution-ref settlement binding, and release
  denial after start;
- unknown and unresolved cost fail-closed behavior;
- claim and idempotency drift;
- kill-switch and revocation rechecks;
- concurrent reservations across separate store instances without
  oversubscription;
- concurrent lease issue without lost updates;
- receipt hash tamper detection;
- correctly hashed impossible transition detection;
- correctly hashed settlement-overage misclassification detection;
- zero-cost reservation denial at an exhausted cost ceiling;
- release rejection once execution is declared started;
- Python state, API, and JSON CLI projection parity.

Evidence: `tests/test_authority_budgets.py`.

## Explicit Non-Goals And Remaining Gaps

This milestone does not add a reservation/settlement mutation API, Control
Center budget controls, provider SDK calls, model calls, billing actions,
external price lookup, browser automation, connector writes, broad shell
execution, production authority, or standing autonomy.

The initial dispatcher now binds policy decision, exact approval validation,
reservation, adapter start, settlement/release, pre-start cancellation, and a
hash-chained dispatch receipt for explicitly injected safe tool adapters. See
`docs/runtime/UAA_AUTHORITY_DISPATCHER_V1.md`. Universal migration of legacy
execution paths, durable mission-step consumption, after-start cancellation,
settlement recovery, paid-provider actual usage proof, typed time windows,
recipient/target constraints, renewal policy, reviewed unresolved-cost
remediation, multi-host storage, and operator budget controls remain missing.
