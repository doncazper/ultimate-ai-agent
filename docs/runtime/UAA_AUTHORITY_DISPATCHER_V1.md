# AuthorityLease Governed Dispatcher V1

Status: implemented Python Core dispatcher, exact filesystem-metadata
MissionRunner, bounded synchronous dependency orchestration, disabled-by-default
local mission worker, durable failure-management state, and redacted API/CLI
inspection; Control Center integration remains missing

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

Queued local mission dispatches add a mandatory execution fence consumed inside
the same locked pre-start boundary. The fence validates the current queue claim,
mission-step claim, worker identity, monotonic generations, expiry, and complete
request fingerprint, then persists only an `execution_fence_ref`. A queued
dispatch without a current exact fence fails closed. Periodic job and step
heartbeats do not grant or cache authority.

The current executable bridge is `ToolRuntimeAuthorityDispatchAdapter`, which
accepts only an explicitly injected descriptor and exactly two tool refs:
deterministic no-op and filesystem metadata. Filesystem execution requires the
fixed `files/read` authority domain/capability pair; deterministic no-op is
fixed to `workspace/execute`. A descriptor cannot relabel either tool into a
different lease domain. The injected safe-root ref-to-path mapping is hashed
into a safe adapter-binding ref and deep-copied into an immutable invocation
snapshot, so a reload or caller mutation cannot redirect a prepared dispatch
to a different physical root.
Filesystem execution also requires the
normalized safe-root ref and safe-path ref to match the action's resource and
path claims; lease constraints and approval scope therefore govern the same
target selected by the invocation. Safe-path refs hash the complete root ref,
so distinct valid root refs cannot collide after normalization. The metadata
result returns bounded facts
such as existence, kind, size, extension, and a safe path ref; it does not
return file content, directory listings, an absolute path, or mutation
authority.

## Durable Lifecycle

The lifecycle is explicit:

1. `prepare` validates the registered adapter and exact target, re-evaluates the
   complete safe-tool runtime policy, requested lease, and exact approval scope
   where required, then reserves budget with the full dispatch fingerprint.
2. A `prepared` receipt durably binds the policy, approval, and reservation.
3. `execute` rechecks lease, kill switch, adapter, the complete immutable
   reservation-to-dispatch binding, cost-budget expiry, and approval revocation
   immediately before start. Approval validation and the durable start claim
   share a revocation critical section, with the authority-state lock acquired
   first to preserve one lock order across prepare and execute.
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
durable start sequence without double allocation. If current authority or cost
posture instead becomes invalid while the dispatch ledger still proves that no
dispatch-start receipt or adapter invocation occurred, the dispatcher may use
an internal, exact fingerprint/execution-bound rollback transition to release
that orphaned start claim and finish `cancelled_before_start`. This is not
after-start cancellation. Once the budget-start claim exists, a standalone
release request remains denied and cannot race an in-flight adapter or erase
its settlement capacity.
If capacity was already released before `execute` observes the inactive
reservation, the dispatcher reuses that durable release receipt and completes
terminal pre-start cancellation instead of stranding `cancellation_pending`.
If a crash leaves capacity reserved without a prepared receipt and a retry is
denied during fresh adapter or cost validation, the dispatcher atomically
releases that exact unclaimed reservation before persisting the denial.
An unchanged replayed reservation also rechecks current lease, kill switch,
approval, adapter, tool-policy, and budget posture before it can reconstruct a
prepared receipt; revoked authority releases the orphan and remains denied.
The dispatcher itself does not own mission-step heartbeats and the current V1
bridge does not claim after-start cancellation, automatic settlement recovery,
or mission retry authority.

## Synchronous Mission Step V1

`MissionStepStore` adds an append-first, fsync-backed, hash-chained ledger for
safe-ref mission-step definitions and receipts. Definitions bind mission, run,
step, capability, adapter, lease, dependency, deadline, and bounded-summary
posture. Claims use a bounded TTL and monotonically increasing generation;
stale owners are fenced, and one immutable dispatch ref plus full authority-
dispatch request fingerprint survives owner reclaim. Claim and deadline
decisions use the store-owned trusted clock; callers cannot supply operation-
level timestamps.

`AuthorityMissionRunner.run_once` consumes that ledger for one synchronous
filesystem-metadata step only. It requires the injected filesystem-metadata
adapter, exact `files/read` authority, one operation, zero estimated cost,
deterministic action/dispatch/idempotency refs derived from the step ref, and
an injected safe-root ref. The runner records intent before calling
`AuthorityDispatcher.prepare` and `execute`; the dispatcher still performs all
current lease, policy, approval, budget, kill-switch, adapter, and target
checks immediately before execution. The runner never mints or caches
authority. It performs one bounded synchronous claim renewal after prepare,
then rechecks the deadline before execute. Expiry cancels through the
dispatcher, releases pre-start budget, and records cancellation evidence
without adapter start. A durable terminal dispatch can be reconciled after
claim expiry without a second adapter start.

A mission step may become `succeeded` only when its terminal receipt equals the
latest durable dispatcher receipt and matches the persisted request
fingerprint, run, lease, adapter, and capability bindings with start,
invocation, and budget-settlement proof. The mission ledger binds the dispatch
receipt and entry-hash refs; caller-asserted success or evidence refs alone are
rejected.

The mission-step ledger stores safe refs and bounded summaries, not tool input,
file content, relative or absolute paths, provider payloads, or raw output.
Append opens now deny symlink and FIFO substitution, require a bounded regular
file, and fsync before returning.

Operators can inspect one exact step through the optional `mission_step_ref`
query on protected `GET /api/runtime/authority-state` or the human-readable
`inspect-authority-mission-step STEP_REF` CLI command. Both use one backend
projection that validates the mission and dispatcher ledgers, hashes dynamic
identity/evidence refs, omits persisted summaries and state paths, and reports
claim freshness separately from durable status. Inspection performs no adapter
invocation, mutation, approval or lease minting, retry, reconciliation, or
request-scoped authority decision.

## Bounded Synchronous Mission Orchestration V1

`SynchronousAuthorityMissionOrchestrator` accepts at most 16 exact
filesystem-metadata steps. Before any execution it validates a closed acyclic
dependency graph, exact mission/run/action/request bindings, and an existing
mission-scoped AuthorityLease whose mission ref is also carried by every action.
It then appends one immutable safe-ref-only durable plan receipt containing the
ordered membership, definition fingerprints, dispatch refs, complete dispatch
request fingerprints, and dependencies. The same plan ref or mission/run pair
cannot be rebound to changed membership, ordering, deadline, target, or request
input.

All bound step definitions are durably created before step one can execute.
Each definition repeats its plan ref, dispatch ref, and request fingerprint, so
an interruption during definition creation can resume only with the identical
plan. Steps run sequentially in stable topological order exclusively through
`AuthorityMissionRunner` and `AuthorityDispatcher`. Authority, approval, kill
switch, budget, adapter, target, and safe-disable posture are therefore
re-evaluated for every step immediately before its durable start claim; the
orchestrator neither invokes adapters directly nor mints or caches authority.
Plan-bound runner execution also requires the accepted plan's exact execution
context. The step claim checks that context and every plan member's terminal
posture while holding the mission-step ledger lock, so a crash window or direct
runner call cannot start later work after fail-fast has activated. Before plan
acceptance, each action receives a pure current lease-policy eligibility check;
the dispatcher still performs the authoritative live check again immediately
before execution.

The dispatch request now carries an optional fingerprint-bound start deadline.
For orchestration it must equal the durable step deadline. Under the authority
and approval locks, the dispatcher captures one trusted admission timestamp,
re-evaluates every expiring lease, approval, and cost-budget input at that exact
instant, and persists the timestamp in the durable start receipt. Expiry at that
admission boundary wins before adapter invocation and releases reserved
capacity. Optional fields are omitted from legacy V1 canonical hash payloads
when null, so pre-upgrade dispatch and mission-step ledgers remain readable.

V1 is fail-fast. A known failed, cancelled, or recovery-required step prevents
independent later work from starting. Declared descendants receive a durable
`dependency_blocked` receipt bound to the terminal dependency receipt and entry
hash; other unscheduled steps receive a durable `fail_fast_halted` receipt
bound to the triggering terminal evidence. Identical replay skips proven
successes; active competing claims return an in-progress posture; there is no
wait loop. Plan-bound definitions cannot be created or claimed unless the
accepted plan proves exact step, definition, dispatch, request-fingerprint, and
dependency membership. This synchronous path is not itself a background
scheduler and adds no parallel fan-out, dynamic output-to-input binding, API or
CLI execution command, or Control Center mutation. The surrounding mission
worker now adds durable approval waits, exact typed retry policy, immutable dead
letters, and append-first mission cancellation without changing the dispatcher
path. Approval decisions and recovery requests are operator intent only; every
later start re-enters the dispatcher's fresh request-scoped checks.

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
start cancels the dispatch without invoking the adapter. Concurrent revocation
cannot complete between a successful validation decision and the fsynced start
claim: whichever acquires the approval-state critical section first defines the
ordered outcome. Caller booleans and approval refs alone do not authorize work.
Caller-selected approval-validation time is rejected so expiry is evaluated
against the trusted local clock. The dispatcher performs a second core-clock
validation after other pre-start work, and approval rollback paths use the same
mutation lock, so neither wall-clock expiry nor failure compensation can bypass
the durable-start check.

The dispatcher also recomputes `CostGovernor` from the typed estimate and
budgets. It rejects caller posture, estimate-ref, decision-ref, integer
micro-USD amount, run-scope, or expiry drift before reservation. A caller-
supplied CostGovernor boolean or ref therefore cannot authorize dispatch by
itself. Expiry is checked again after approval and all other pre-start work, at
the durable start boundary.

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
the dispatch-start receipt replays that same claim when all bindings and
authority remain valid, or performs the exact internal orphan rollback above
when they do not. Before either outcome, the dispatcher compares lease, action,
approval, cost, reservation values, fingerprint, execution, and initial receipt
identity across both ledgers; correctly rehashed semantic drift cancels rather
than authorizing execution. A crash after adapter start is never treated as safe
to replay.

## Verified Acceptance Cases

The focused `tests/test_authority_dispatcher*.py` modules cover:

- a useful filesystem metadata dispatch with no raw content or absolute path in
  durable evidence;
- exact approval success, missing approval denial, out-of-scope denial, and
  revocation immediately before start, concurrent revocation/start
  serialization, plus caller-time rejection;
- local CostGovernor recomputation and caller posture/ref/amount binding;
- non-finite estimate or budget denial without conversion failure;
- mismatched adapter execution-ref rejection with a readable failed terminal
  receipt;
- lease revocation between prepare and start;
- pre-start cancellation, capacity release, cancellation idempotency conflict,
  collision-safe release keys, and cancellation-claim crash recovery;
- concurrent replay with exactly one adapter invocation, losing-reservation
  release, orphaned-reservation recovery, start-claim crash replay, and exact
  rollback when a budget start is orphaned before dispatch start;
- release denial after durable start while the adapter is in flight;
- denial of dispatch-bound settlement before start and terminal reconciliation
  of a reservation released before execution;
- dispatcher-owned settlement while competing public settlement is denied, and
  release of crash-orphaned capacity before an early terminal denial;
- safe-tool runtime policy denial before reservation/start and fresh authority
  revalidation before an orphaned reservation can recover to `prepared`;
- descriptor and safe-root mapping drift cancellation, fixed tool authority
  domains, immutable safe-root snapshots, implementation/manifest-bound
  adapter identity, descriptor-relative no-follow metadata traversal, and an
  explicit no-op/filesystem-metadata tool bridge allowlist;
- approval-scope narrowing that cannot widen, detached validated approval
  and lease state, safe-ref-only revocation reasons, and monotonic durable
  revocation through an fsynced restart-replayed tombstone;
- action/approval replay conflict, dispatch idempotency conflict, receipt hash
  tampering, cross-ledger semantic drift, mismatched injected lease sources,
  start-boundary cost expiry, and non-mutating fresh read inspection.
- mission-step claim races, stale-owner fencing, immutable dispatch request
  fingerprints, dependency denial, trusted-clock expiry before claim and after
  prepare with pre-start cancellation/budget release, forged-success rejection,
  cross-ledger terminal binding, hash and semantic tamper rejection, exact
  filesystem-metadata execution, revoked-lease denial, terminal replay after a
  simulated runner crash, and denial of binding drift or the no-op adapter;
- mission-step ledger redaction proof that excludes raw safe-root paths,
  relative paths, and file contents.

The focused dispatcher, budget, durable plan, durable mission-step,
mission-runner, and mission-orchestrator suites are the acceptance source for
this milestone. Broader repo checks remain required before merge.

## Explicit Non-Goals And Remaining Gaps

This milestone adds no API mutation route, Control Center execution control,
generic dynamic registry, runtime import, unrestricted shell/subprocess call,
provider/model call, browser action, connector write, network expansion,
public distribution, production authority, or standing autonomy.

The dispatcher is not yet the universal route for legacy executable lanes.
Durable missions still need mission-wide retry and cost budgets, safe
after-start cancellation, settlement recovery, mission completion receipts,
restart-time approval-request resolver proof, Control Center mission controls,
and broader exact adapters. Dead letters
remain terminal and require a new plan and fresh request-scoped authority;
recovery intent does not replay them. The local worker supplies bounded job and
step heartbeats but does not cache authority; every resumed start re-enters the
dispatcher. Each future adapter must be promoted as an exact descriptor and
tested lane; V1 does not grant a broad capability class.
