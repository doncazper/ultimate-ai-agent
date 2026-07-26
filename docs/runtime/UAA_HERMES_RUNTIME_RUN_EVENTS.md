# Proof-Backed Goals And Durable Run Events

Status: UAA parity-gap closure Phase 04, local durable state implemented.

The Python Agent Core owns a persistent founder/operator goal journal and a
durable event source for accepted local run types. The implementation replaces
the old sample-event success path used by `GET /api/runtime/run-events`.
Control Center and CLI render the same backend-owned state; their fallbacks
show an explicit empty or unavailable state and do not invent goals, runs,
events, receipts, or completion.

## Persistent goals

Each goal stores a stable safe ref, bounded objective and desired outcome,
success criteria, constraints, in-scope resource refs, stop condition, budget,
links, evidence refs, lifecycle state, version, and timestamps. The append-first
goal journal is atomically replaced under a single-writer lock and checks its
monotonic versions, idempotency refs, predecessor hashes, entry hashes, and
deterministic entry refs on every read.

Supported local metadata transitions are create, edit, pause, resume, block,
wait, cancel, clear, request completion, and verify completion. Every API or CLI
mutation requires an idempotency ref and captures one request-scoped
`LocalApprovalAuthority` decision bound to the exact operation, subject,
payload fingerprint, and scope. The Core store revalidates the complete typed
binding rather than accepting caller-supplied approval strings, and the raw
journal store is not exported as a public runtime-gateway surface. That
decision grants no standing authority and cannot execute a runtime action.

`complete_requested` is distinct from `verified_complete`. Verification fails
closed unless the current goal version links the exact run and the durable event
store already contains a matching goal-bound receipt and proof. Successful
verification records a terminal `completion_verified` event. Model output is
never authoritative. The verified goal snapshot retains the exact run,
evidence, receipt, proof, and verifier refs. On restart, the Core reconciles
any verified goal whose terminal event commit was interrupted, appends the
same deterministic idempotent event, and then accepts an exact retry of the
original transition without advancing the goal version. Completion preflight
and commit hold the run-event writer lock, so an already-terminal run is
rejected before the goal journal changes.

## Durable events

Accepted event streams are limited to `local_read_task` and
`local_metadata_action`. Every event stores:

- a stable event ref and run ref;
- a monotonic per-run sequence and timestamp;
- an event kind and bounded redacted summary;
- exact goal, plan, proof, receipt, idempotency, and authority-decision refs;
- a predecessor hash and event hash; and
- explicit denial of raw runtime-payload persistence.

The store validates deterministic event-ref binding, hashes, predecessor
continuity, sequence order, per-run type consistency, and duplicate
idempotency refs on every read. Reusing an idempotency ref with a different
payload is rejected. A bounded durable tombstone/fingerprint index preserves
exact idempotent replay after event-payload retention and fails closed at its
capacity instead of evicting accepted idempotency history. Completion events
require matching prior receipt evidence. Cancelled, verified-complete,
terminal-failure, and dead-letter events require receipt and proof refs; those
streams are terminal and late success events are rejected.

Accepted `RuntimeGateway` local-model and governed-command receipts are
projected at the Python Core boundary as `run_started` plus
`receipt_recorded`. API and CLI read paths also reconcile already-durable
RuntimeGateway receipts idempotently after a process interruption. Blocked or
approval-pending invocations are not projected as accepted runs.

Retention is bounded per run. Cursor replay returns explicit `ok`,
`unknown_run`, `stale_cursor`, or `retention_loss` state with the retained
anchor, next cursor, and gap posture. Replay never returns duplicates. Atomic
receipt persistence is independent of consumers, so a slow or disconnected
reader cannot block the writer or create an unbounded in-memory queue.
The goal journal, run events, and idempotency index use a private `0700` state
directory and `0600` files.

## Operator surfaces

- `GET /api/runtime/goals`
- `GET /api/runtime/goals/{goal_ref}`
- `POST /api/runtime/goals`
- `POST /api/runtime/goals/{goal_ref}/edit`
- `POST /api/runtime/goals/{goal_ref}/transition`
- `GET /api/runtime/run-events?run_ref=...&after_sequence=...&limit=...`
- `scripts/dev/uaa_runtime.py goals-list`
- `scripts/dev/uaa_runtime.py goal-show`
- `scripts/dev/uaa_runtime.py goal-create`
- `scripts/dev/uaa_runtime.py goal-edit`
- `scripts/dev/uaa_runtime.py goal-transition`
- `scripts/dev/uaa_runtime.py inspect-run-events`
- Control Center `/runtime` goal and durable-event summary

The existing mission-control boundary keeps run cancellation, approval
decisions, and dead-letter recovery on separate exact routes. Those routes
re-evaluate their own current policy/approval/lease posture; a durable goal or
event ref does not authorize them.

## Evidence and recovery coverage

Focused tests cover idempotent create/edit/transition behavior, optimistic
version conflicts, restart reconstruction, cursor reconnect, bounded retention,
unknown and stale cursors, Unicode summaries, reordered/gapped sequences,
field and wrapper tampering, type substitution, receipt-bound completion,
terminal proof requirements, pre-commit terminal fences, interrupted
terminal-event commit recovery, exact transition retry, retained idempotency
tombstones, private filesystem modes, malformed idempotency refs, accepted
RuntimeGateway producer wiring, approval wait/resume, controlled worker-restart
evidence, and a second cancelled run. API and CLI are compared after process-state
reconstruction, while the Control Center tests consume the same typed read
model and reject mock completion. A newly created Control Center goal starts
with empty relationship lists; the UI never fabricates plan, run, Action
Inbox, Work Board, or evidence records.

The broader AuthorityLease mission worker remains the owner of cancellation
stages, approval expiry/reject/edit/resume, stale claims, orphan recovery,
duplicate worker identity, dead letters, restart admission fences, and
retryable-versus-terminal failure execution. Phase 04 records and replays their
safe refs; it does not duplicate or bypass that worker.

## Blocked

No live SSE or WebSocket transport is enabled because no exact live-streaming
authority lane has been accepted. The read route accepts no control messages.
Delegated run creation, unrestricted retry/resume, runtime model calls,
provider SDK calls, unrestricted shell execution, browser automation, web
fetching, connector writes, plugin runtime import, background production
authority, remote execution, public distribution, and raw prompt, response,
provider payload, runtime payload, log, path, or credential persistence remain
blocked.

Hash chains detect durable-state disagreement and tampering; they are not
signatures and do not establish an external identity.
