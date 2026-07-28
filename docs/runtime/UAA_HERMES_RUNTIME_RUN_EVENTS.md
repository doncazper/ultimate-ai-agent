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
Goal text is accepted only under the explicit
`operator_authored_redacted_summary_only` posture and rejects multiline,
prompt-like, response-like, or secret-like raw-content shapes before durable
persistence.
Edit evidence is append-only: newly supplied evidence refs are unioned with
the prior authoritative snapshot instead of replacing its audit history.
Every transition journal entry also retains the validated reason ref, covered
by the entry hash, so lifecycle intent remains readable after restart.
The complete audit chain is bounded by explicit entry and byte capacities.
Mutations fail closed before either capacity is crossed, so a long-lived goal
cannot make the journal or the cost of each atomic rewrite grow without limit;
the existing hash-linked history is never silently truncated or compacted away.

Supported local metadata transitions are create, edit, pause, resume, block,
wait, cancel, clear, restore, request completion, and verify completion. Restore
replays the exact durable snapshot immediately before the latest clear, advances
the version, and remains approval-bound and idempotent; clear is therefore
hidden by default without being an irreversible delete. Every API or CLI
mutation requires an idempotency ref and captures one request-scoped
`LocalApprovalAuthority` decision bound to the exact operation, subject,
payload fingerprint, and scope. The Core store revalidates the complete typed
binding rather than accepting caller-supplied approval strings, and the raw
journal store is not exported as a public runtime-gateway surface. That
decision grants no standing authority and cannot execute a runtime action.

`complete_requested` is distinct from `verified_complete`. Verification fails
closed unless the current goal version links the exact run and the durable event
store already contains a matching goal-bound receipt and proof. Every ordered
success criterion must also bind to a criterion proof ref present in that exact
trusted receipt; the built-in verifier hash covers the criterion/proof pairs,
goal version, run, receipt, primary proof, and plan. Successful verification
records all of those bindings in a terminal `completion_verified` event. Model
output is never authoritative. The verified goal snapshot retains the exact run,
receipt-derived plan, evidence, receipt, primary proof, criterion proofs, and
verifier refs. On the next
mutating path after restart, the Core reconciles any verified or subsequently
cleared goal whose terminal event commit was interrupted, appends the same
deterministic idempotent event with the original transition approval decision,
and then accepts an exact retry without advancing the goal version. Completion
preflight and commit hold the run-event writer lock, so an already-terminal run
is rejected before the goal journal changes.

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
capacity instead of evicting accepted idempotency history. Integrity-checked
tombstones also preserve completion-bearing receipt and proof evidence after
the replay payload itself is evicted. Completion events require matching prior
receipt evidence. Cancelled, verified-complete,
terminal-failure, and dead-letter events require receipt and proof refs; those
streams are terminal and late success events are rejected.
The event journal and tombstone history are one consistency boundary: a missing
or empty event journal with surviving accepted tombstones is corruption, not an
empty runtime. Both stores have explicit encoded-byte limits, and a candidate
append preflights the complete next event and tombstone images before either
file is replaced.

Successful `RuntimeGateway` local-model and governed-command receipts are
projected at the Python Core boundary as `run_started` plus
`receipt_recorded`. Deterministically unsuccessful or indeterminate attempts
instead project `run_started` plus proof-backed `failed_terminal`, so their
receipts can never satisfy goal completion. Public metadata writers reject both
receipt and completion events; only receipt-validated Core producers may append
them. Before runtime execution, a private durable reservation
secures the exact two-event projection capacity without holding the event lock
across the bounded runtime call. The reservation is then bound to the exact
receipt-derived event keys and consumed atomically under the writer lock.
Reservation identity is deterministic for the operation idempotency ref, and
each reservation is a short bounded lease longer than the maximum supported
runtime call. Exact retries reuse the lease, while expired crash leftovers are
reclaimed under the same writer lock before capacity is counted.
Mutating API and CLI paths reconcile already-durable RuntimeGateway receipts
idempotently after a process interruption. Reconciliation reads the tombstone
index once and selects only records whose exact projection keys remain absent;
already-projected history is not rewritten for every new invocation.
`GET /api/runtime/run-events` and CLI inspection remain strictly read-only.
Blocked or approval-pending invocations are not projected as accepted runs.
Projection-capacity or corruption failures are returned through redacted API
and CLI error envelopes rather than escaping as unstructured failures. Local
storage failures are normalized to the same safe contract, and goal mutations
remain in the governed-runtime targeted rate-limit group.
When CLI `--state-dir` is supplied, goal state is derived from the same
`goal_runtime` child used by the API for that runtime store. An unavailable or
invalid directory, corrupt journal, or malformed inspection ref returns a
bounded message without exposing the supplied path or a traceback.

Retention is bounded per run. Cursor replay returns explicit `ok`,
`unknown_run`, `stale_cursor`, or `retention_loss` state with the retained
anchor, next cursor, and gap posture. Replay never returns duplicates. Atomic
receipt persistence is independent of consumers, so a slow or disconnected
reader cannot block the writer or create an unbounded in-memory queue.
The goal journal, run events, idempotency index, and projection reservations
use a private `0700` state directory and `0600` files. The public service
exposes a read-only event facade; metadata event writes require one exact
request-scoped local approval, while receipt and completion events remain
trusted Core producer paths.

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

The exact-goal read and `goal-show` CLI return the bounded, content-free mutation
provenance chain alongside the current goal. Provenance includes operation,
version, idempotency, request fingerprint, approval, reason, and hash refs, but
does not repeat raw request payloads or goal text.

Control Center retains the exact pending create, edit, or transition request and
idempotency ref until the
post-mutation authoritative refresh succeeds. A transient refresh failure can
therefore only replay the same mutation; it cannot silently create a second
goal, edit, or transition. Accepted create, edit, and transition responses are
applied as local
authoritative snapshots before the follow-up read; a refresh failure cannot
leave the UI on a stale version or misreport an accepted mutation as rejected.
The follow-up event read is bound to the same selected backend-truth envelope,
and every event preview is checked field-by-field before display.
The run-events operator read model includes cleared goals so its exact restore
control remains reachable, while the dedicated default goal listing continues
to hide cleared records.

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
tombstones, pre-execution projection-capacity fencing, read-only inspection,
completion after payload retention, crash-reservation recovery, bounded goal
journal capacity, redacted projection failures, private writer authority,
private filesystem modes, malformed idempotency and run refs, exact clear
restore, custom-state CLI/API parity, retained create idempotency after refresh
failure, append-only edit evidence, hash-bound transition reasons, redacted CLI
inspection failures, cleared-goal restore visibility, typed budget/link edits,
trusted receipt-producer enforcement, successful-versus-failed
RuntimeGateway projection, accepted RuntimeGateway producer wiring, approval wait/resume,
controlled worker-restart evidence, and a second cancelled run. API and CLI
are compared after process-state reconstruction, while the Control Center
tests consume the same typed read model and reject mock completion. A newly
created Control Center goal starts with empty relationship lists; the UI never
fabricates plan, run, Action Inbox, Work Board, or evidence records.

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
