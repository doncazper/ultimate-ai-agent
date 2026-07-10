# AuthorityLease Durable Budget Ledger V1

Status: implemented Python Core budget foundation; dispatcher and Control Center
mutation integration remain missing

Date: 2026-07-10

## Implemented Boundary

AuthorityLease V1 now supports two typed, integer constraints:

- `operation_budget`: maximum cumulative operation count for one lease;
- `cost_budget_microusd`: maximum cumulative cost in integer micro-USD for one
  lease.

`AuthorityBudgetStore` records reservations, settlements, releases, and denials
in `authority_budget_receipts.jsonl` under `UAA_AUTHORITY_STATE_DIR`. The ledger
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
- a complete `AuthorityActionRequest` that independently evaluates to `allow`;
- exact operation and estimated-cost claims matching the action's typed
  constraint claims;
- structured cost-estimate and CostGovernor decision refs;
- an explicit CostGovernor allowed posture;
- an idempotency ref and bounded safe summary.

The store re-reads active leases while holding the authority-state lock and
rechecks policy outcome, lease identity, typed budget constraints, cumulative
usage, unresolved actual cost, revocation/expiry, and the local kill switch.
Missing budgets, unknown estimated cost, CostGovernor denial, claim drift,
policy denial, exhausted capacity, or stale lease binding produces a durable
denial receipt and no reservation.

CostGovernor refs are a required integration contract, not self-sufficient
proof of a CostGovernor evaluation. The future central dispatcher must supply
them from the same verified dispatch envelope before any executable adapter is
bound to this store.

## Settlement And Release

After execution starts, a reservation must be settled with actual operation
count, actual cost plus its safe ref, execution status, and evidence refs. The
ledger always records actual overage. A settlement exceeding its reservation or
lease ceiling becomes `settled_overage`; any unreviewed reservation overage
freezes future capacity even when actual usage remains below the lease ceiling.
When actual cost is unknown, the settlement becomes
`settled_cost_unresolved` and all later reservations for that lease fail closed
until a future reviewed remediation contract exists.

A reservation may be released only through a request whose typed contract says
execution has not started. Release frees the reserved capacity and records the
reason ref. This V1 store cannot independently prove adapter start state; that
binding belongs in the central dispatcher and remains missing.

## Replay, Corruption, And Read Surfaces

Every operation fingerprints its full request. Repeating the same idempotency
ref and fingerprint returns a non-persisted `replayed` view; changing operation
or request content raises an idempotency conflict. Full ledger history is
validated on every transaction. Duplicate idempotency or reservation history,
invalid receipt semantics, impossible reservation transitions, follow-up
binding drift, broken previous-hash linkage, or changed entry content fails
closed as ledger corruption.

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
execute, approve, or mint authority.

## Verified Acceptance Cases

Focused tests cover:

- exact constraint evaluation and applied constraint refs;
- reserve, replay, settle, overage, release, and cumulative exhaustion;
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

Before an executable capability can claim end-to-end durable budgeting, UAA
still needs a central dispatcher that atomically binds policy decision,
LocalApprovalAuthority validation where required, reservation, adapter start,
settlement/release, cancellation, and one receipt envelope. Typed time windows,
recipient/target constraints, renewal policy, reviewed unresolved-cost
remediation, multi-host storage, and operator budget controls also remain
missing.
