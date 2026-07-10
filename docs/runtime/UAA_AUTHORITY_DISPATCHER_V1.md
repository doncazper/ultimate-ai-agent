# AuthorityLease Governed Dispatcher V1

Status: implemented Python Core dispatcher for explicitly injected safe tool
adapters; durable mission, API, CLI mutation, and Control Center integration
remain partial or missing

Date: 2026-07-10

## Implemented Boundary

`AuthorityDispatcher` is the first central execution boundary that consumes an
`AuthorityLease` budget reservation. It binds one exact dispatch request to:

- an `AuthorityActionRequest`, active lease ref, adapter ref, capability ref,
  run ref, request fingerprint, and redacted adapter-configuration fingerprint;
- current AuthorityLease policy and kill-switch posture;
- exact `LocalApprovalAuthority` validation when policy or adapter posture
  requires it;
- a typed CostEstimate and run-scoped CostBudget set, locally recomputed
  CostGovernor decision, deterministic estimate/decision refs, and a typed
  operation/cost reservation whose cost covers the adapter's declared failure
  cost;
- a durable budget-start claim plus adapter-start receipt written before
  invocation;
- actual operation/cost settlement and safe evidence/output refs after
  invocation;
- pre-start cancellation, budget release, idempotent replay, recovery posture,
  rollback ref, and safe-disable ref.

Dispatch receipts are stored in `authority_dispatch_receipts.jsonl` under
`UAA_AUTHORITY_STATE_DIR`. They are append-first, fsync-backed, SHA-256
hash-chained, full-history transition checked, and protected by the shared
authority-state single-writer lock. Durable receipts contain safe refs and
bounded summaries only. Adapter input is fingerprinted but is not copied into
the receipt ledger.

The current executable bridge is `ToolRuntimeAuthorityDispatchAdapter`, which
accepts only an explicitly injected descriptor and exactly two tool refs:
deterministic no-op and filesystem metadata. Filesystem execution requires the
fixed `files/read` authority domain/capability pair; deterministic no-op is
fixed to `workspace/execute`. A descriptor cannot relabel either tool into a
different lease domain. The injected safe-root ref-to-path mapping is hashed
into a safe adapter-binding ref, so a restart cannot redirect a prepared
dispatch to a different physical root without pre-start cancellation.
Filesystem execution also requires the
normalized safe-root ref and safe-path ref to match the action's resource and
path claims; lease constraints and approval scope therefore govern the same
target selected by the invocation. The metadata result returns bounded facts
such as existence, kind, size, extension, and a safe path ref; it does not
return file content, directory listings, an absolute path, or mutation
authority.

## Durable Lifecycle

The lifecycle is explicit:

1. `prepare` validates the registered adapter and exact target, re-evaluates the
   requested lease, validates exact approval scope where required, and reserves
   budget with the full dispatch fingerprint.
2. A `prepared` receipt durably binds the policy, approval, and reservation.
3. `execute` rechecks lease, kill switch, adapter, budget, and approval
   revocation immediately before start.
4. The budget ledger first records a replay-safe `started` transition bound to
   the dispatch fingerprint and execution ref; the dispatch ledger then fsyncs
   its `started` receipt before the adapter is invoked.
5. Adapter success or failure is settled against the reservation and a
   terminal `succeeded` or `failed` receipt binds evidence and actual cost.
6. A prepared dispatch may be claimed as `cancellation_pending`; capacity is
   released before `cancelled_before_start` becomes terminal.

A process interruption after `started` is fail-closed and visible as
`recovery_required`; the dispatcher will not invoke the adapter again under the
same idempotency key. A process interruption after a cancellation claim is also
visible and retryable with the exact cancellation idempotency and reason refs.
If the process stops after the budget-start claim but before the dispatch-start
receipt, the exact start claim replays and the unchanged request can finish the
durable start sequence without double allocation. Once the budget-start claim
exists, a standalone release request is denied and cannot race an in-flight
adapter or erase its settlement capacity.
The current V1 bridge does not claim after-start cancellation, automatic
settlement recovery, heartbeat ownership, or mission retry authority.

## Approval And Budget Binding

Budget reservation now understands AuthorityLease policy outcomes that require
an operator answer. An `ask` decision may reserve only when a trusted validator
confirms an exact `LocalApprovalAuthority` grant. The approval validation must
bind the action ref as both subject and requested action, and its resource set
must exactly equal the lease ref, adapter ref, and action resource refs.

The budget receipt stores the approval ref, a deterministic validation ref, and
whether approval was effectively required. Dispatch receipts separately retain
the adapter's intrinsic approval posture, so a policy-required approval is not
mistaken for adapter configuration drift. These bindings follow the reservation
through start, settlement, or release. Approval revocation between prepare and
start cancels the dispatch without invoking the adapter. Caller booleans and
approval refs alone do not authorize work. Caller-selected approval-validation
time is rejected so expiry is evaluated against the trusted local clock.

The dispatcher also recomputes `CostGovernor` from the typed estimate and
budgets. It rejects caller posture, estimate-ref, decision-ref, integer
micro-USD amount, run-scope, or expiry drift before reservation. A caller-
supplied CostGovernor boolean or ref therefore cannot authorize dispatch by
itself.

## Replay, Concurrency, And Corruption

The dispatcher rejects dispatch-ref, action-ref, request-fingerprint, or
idempotency drift. One action ref can bind to only one durable dispatch, so an
approval cannot be replayed by cloning the action into a new dispatch envelope.
Concurrent callers using the same exact request can produce only one adapter
start. Every ledger read verifies hash linkage, entry hashes, allowed lifecycle
transitions, immutable policy/approval/budget bindings, action-to-dispatch
identity, adapter-configuration continuity, budget-start/execution-ref
continuity, and cancellation-ref continuity. Correctly rehashed semantic drift
therefore still fails closed.

Budget reservation and dispatch receipts are separate fsync-backed ledgers.
Crash safety comes from deterministic phase idempotency and recovery states,
not from claiming a cross-file database transaction. A crash after reservation
but before the prepared receipt is recoverable by replaying the same prepare
request; if a competing identity wins first, the unclaimed replayed reservation
is released deterministically. A crash after the budget-start claim but before
the dispatch-start receipt replays that same claim. A crash after adapter start
is never treated as safe to replay.

## Verified Acceptance Cases

`tests/test_authority_dispatcher.py` covers:

- a useful filesystem metadata dispatch with no raw content or absolute path in
  durable evidence;
- exact approval success, missing approval denial, out-of-scope denial, and
  revocation immediately before start, plus caller-time rejection;
- local CostGovernor recomputation and caller posture/ref/amount binding;
- non-finite estimate or budget denial without conversion failure;
- mismatched adapter execution-ref rejection with a readable failed terminal
  receipt;
- lease revocation between prepare and start;
- pre-start cancellation, capacity release, cancellation idempotency conflict,
  collision-safe release keys, and cancellation-claim crash recovery;
- concurrent replay with exactly one adapter invocation, losing-reservation
  release, orphaned-reservation recovery, and start-claim crash replay;
- release denial after durable start while the adapter is in flight;
- descriptor and safe-root mapping drift cancellation, fixed tool authority
  domains, and an explicit no-op/filesystem-metadata tool bridge allowlist;
- action/approval replay conflict, dispatch idempotency conflict, receipt hash
  tampering, and non-mutating fresh read inspection.

The focused dispatcher and budget suite is the acceptance source for this
milestone. Broader repo checks remain required before merge.

## Explicit Non-Goals And Remaining Gaps

This milestone adds no API mutation route, Control Center execution control,
generic dynamic registry, runtime import, unrestricted shell/subprocess call,
provider/model call, browser action, connector write, network expansion,
background worker, public distribution, production authority, or standing
autonomy.

The dispatcher is not yet the universal route for legacy executable lanes.
Durable missions still need step ownership, dependency scheduling, approval
waits, heartbeat/lease renewal, retry budgets, after-start cancellation,
settlement recovery, dead-letter handling, CLI/API/Control Center parity, and
one end-to-end delegated mission proof. Each future adapter must be promoted as
an exact descriptor and tested lane; V1 does not grant a broad capability class.
