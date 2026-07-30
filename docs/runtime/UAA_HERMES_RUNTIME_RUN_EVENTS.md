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
deterministic entry refs on every read. A separately replaced head manifest
anchors the exact entry count, terminal entry hash, and full idempotency-set
fingerprint. The first journal commit is preceded by a durable genesis intent
that binds the exact first entry, journal image, and head manifest; interrupted
first commits can recover only that independently bound candidate. Every later
append likewise installs a generic durable intent binding the old head, exact
next entry, full next journal image hash, and next head before replacing the
journal. Controlled recovery validates the exact typed mutation payload,
resulting snapshot transition, and approval-ledger provenance under the
approval-to-journal lock order before advancing either head. An unanchored
first journal, an unbound one-entry-ahead journal, a truncated prefix, a copied
approval binding, or a journal/head/intent disagreement fails closed.
Goal text is accepted only under the explicit
`operator_authored_redacted_summary_only` posture and rejects multiline,
prompt-like, response-like, or secret-like raw-content shapes before durable
persistence or approval preparation. The same canonical secret detector guards
durable event summaries. POSIX, Windows drive, UNC, and file-URI absolute path
shapes are also rejected without persisting the supplied content.
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

Control Center goal mutations also carry a collision-resistant submission ref.
Before the goal mutation begins, the Core durably records the exact validated
request, idempotency ref, and submission-evidence ref in a bounded,
integrity-checked local recovery store. `GET /api/runtime/run-events` reports
each retained submission as pending, committed, or terminally rejected by
reconciling it against the same locked goal-journal generation, including
bounded historical snapshots. A commit is recognized only when the journal
entry binds the same operation, goal posture, idempotency ref, typed request
fingerprint, submission evidence, and full submission-record fingerprint;
safe-shaped evidence refs alone cannot prove a commit. Pending records are
admitted only when the encoded store still has enough reserved space for every
pending envelope to become a maximum-sized terminal rejection after a restart.
The bounded goal-mutation provenance projection carries that safe submission
fingerprint for create, edit, and transition entries without exposing request
content.
Reserved Control Center submission evidence is rejected unless the exact
backend-owned recovery envelope exists. Terminal recovery records carry a
durable resolution timestamp for deterministic UI ordering; committed recovery
remains authoritative after bounded goal-evidence compaction.
Terminal deterministic mutation failures are
durably bound to a safe rejection-reason ref before the response is returned;
the rejected identity cannot be replayed, while Control Center releases its
pending state so the operator can revise the request and submit a new identity.
After navigation, reload, or a lost response, Control Center either adopts and
replays the exact pending envelope, suppresses the retry when the journal proves
it committed, or reports the durable rejection. Multiple pending envelopes fail
closed to CLI inspection. This recovery contract does not mint approval, expand
authority, or permit a caller to substitute a new request under an existing
submission ref.

`complete_requested` is distinct from `verified_complete`. Verification fails
closed unless the current goal version links the exact run and the durable event
store already contains a matching goal-bound receipt and proof. Every ordered
success criterion must also bind to a criterion proof ref present in that exact
trusted terminal receipt. The receipt carries the exact goal/version,
criterion ID, proof ref, verifier ref, and evaluator-receipt ref for each
criterion; completion derives the ordered proof set from those trusted durable
bindings rather than accepting client proof refs as evaluator provenance. The
built-in verifier hash covers those criterion bindings, goal version, run,
receipt, primary proof, and plan. Successful verification
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
An invocation that claims a `goal-ref:` mission is rejected before either the
command or local-model adapter runs unless that exact ref exists in the durable
goal journal and its current lifecycle state is `active`. The Core completes
projection reconciliation and capacity reservation first, then holds the
canonical approval-to-journal admission locks through adapter dispatch so a
pause, block, wait, completion request, cancellation, clear, or verified
completion cannot race between the state check and execution. An exact
already-committed invocation replay may still return its historical durable
result after a later goal transition; it cannot cause a new adapter call.
Non-goal mission refs retain their existing governed behavior.
Historically accepted receipts with opaque goal-shaped missions are left
unprojected and recorded once in a bounded, content-bound incompatibility
quarantine whose independently persisted head binds the exact durable receipt
and the authoritative goal-journal absence generation. Every later skip
revalidates that the claimed goal is still absent; a subsequently admitted
goal makes the receipt eligible for projection instead of letting a recomputed
quarantine suppress it. Quarantine admission uses a recoverable append intent
across the JSONL and independent head, and capacity exhaustion fails closed
instead of silently omitting an accepted historical receipt. Aggregate
recovery detects that exact intent and finishes it under the quarantine writer
lock before returning the authoritative snapshot.
The event journal and tombstone history are one consistency boundary: a missing
or empty event journal with surviving accepted tombstones is corruption, not an
empty runtime. Both stores have explicit encoded-byte limits, and a candidate
append preflights the complete next event and tombstone images before either
file is replaced. The proof-ref and receipt-ref arities and the event,
tombstone, and first-journal-generation reservation sizes are derived from the
same bounded Pydantic maximum envelopes. A schema-valid maximum record
therefore cannot outgrow a separately maintained reservation constant.
Every accepted append first persists a bounded intent binding the previous
independent generation head, exact next event/tombstone/source record, and next
head. The event, tombstone, and trusted-source projections are then installed
before the new head and intent removal. Read-only paths fail closed while an
intent remains; the next mutating path may finish only that exact precommitted
generation. Rolling the event journal and tombstone index back together to an
older valid prefix therefore disagrees with the independent head instead of
silently discarding an accepted run.
Authority-bearing receipt and terminal events cannot use the self-attested
trusted-Core source posture. They must bind to an exact independent
RuntimeInvocationStore receipt/evaluator record or to the exact durable goal
journal completion entry. Runtime-backed events must also equal the complete
canonical event requests derived from that immutable receipt. RuntimeGateway
mutation locks retain the validated state-root directory descriptor through
lock creation and every ledger/safe-disable write, so an exchanged real
ancestor cannot redirect evidence into a substituted tree.

Successful `RuntimeGateway` local-model and governed-command receipts are
projected at the Python Core boundary as `run_started` plus
`receipt_recorded`. Deterministically unsuccessful or indeterminate attempts
instead project `run_started` plus proof-backed `failed_terminal`, so their
receipts can never satisfy goal completion. Public metadata writers reject both
receipt and completion events; only receipt-validated Core producers may append
them. Every newly written trusted event also binds a separately persisted
source record to the exact durable runtime invocation or completion journal
entry. Retained events and tombstones revalidate that source generation before
replay or completion use. The trusted Core idempotency namespaces are reserved
at both public approval preparation and append, so an operator metadata event
cannot preoccupy a future projection key. Before runtime execution, a private durable reservation
secures the exact two-event projection capacity without holding the event lock
across the bounded runtime call. The reservation is then bound to the exact
receipt-derived event keys and consumed atomically under the writer lock.
Reservation identity is deterministic for the operation idempotency ref, and
each reservation is a short bounded lease longer than the maximum supported
runtime call. Exact retries reuse the lease, while expired crash leftovers are
reclaimed under the same writer lock before capacity is counted. After mission
admission and immediately before adapter dispatch, the Core revalidates
capacity and refreshes that exact lease; a request delayed behind other mission
locks therefore fails before execution or receives a fresh bounded guarantee.
The durable adapter-start marker is also an ownership claim: exactly one caller
may cross a receiptless adapter boundary, while concurrent exact replays observe
an in-progress result and do not execute the adapter. Command dispatch
revalidates the current authority lease and operator safe-disable state inside
the same locked mutation that records that claim. Historical invocations that
predate the dispatch protocol can replay only an already-durable immutable
receipt; receiptless legacy records remain fail closed.
Mutating API and CLI paths reconcile already-durable RuntimeGateway receipts
idempotently after a process interruption. Reconciliation reads the tombstone
index once and selects only records whose exact projection keys remain absent;
already-projected history is not rewritten for every new invocation.
`GET /api/runtime/run-events` and CLI inspection do not initialize absent
state or grant authority; they may finish only an independently precommitted
exact recovery intent before reading.
Their aggregate event, summary, replay, goal-lifecycle, and submission response
is built from one canonical approval-ledger, event, goal-journal, then
submission snapshot boundary. Goal list, detail, mission preflight, and durable
event readers use the same approval-first order and validate every
approval-bearing journal/event record against the exact durable approval
decision before presenting it as authoritative truth. Mutation paths preserve
the same dependency order, and absent-lock reads use bounded generation
validation rather than creating or changing lock state.
Goal commit and terminal submission rejection both hold the goal-journal lock
before the submission lock. The submission state is rechecked while both are
held, so concurrent exact retries choose one terminal committed-or-rejected
result and cannot leave a journal entry paired with a rejected submission.
Blocked or approval-pending invocations are not projected as accepted runs.
Projection-capacity or corruption failures are returned through redacted API
and CLI error envelopes rather than escaping as unstructured failures. Local
storage failures are normalized to the same safe contract, and goal mutations
remain in the governed-runtime targeted rate-limit group.
When CLI `--state-dir` is supplied, goal state is derived from the same
`goal_runtime` child used by the API for that runtime store. An unavailable or
invalid directory, corrupt journal, or malformed inspection ref returns a
bounded message without exposing the supplied path or a traceback.
Every goal CLI command honors `--json` on failure with a stable redacted code;
validation, conflict, corruption, and storage failures never require parsing a
human stderr sentence.

Retention is bounded per run. Cursor replay returns explicit `ok`,
`unknown_run`, `stale_cursor`, or `retention_loss` state with the retained
anchor, next cursor, and gap posture. Replay never returns duplicates. Atomic
receipt persistence is independent of consumers, so a slow or disconnected
reader cannot block the writer or create an unbounded in-memory queue.
The approval ledger, goal journal, goal-submission recovery store, run events,
idempotency index, and projection reservations use a private `0700` state
directory and `0600` files. Every state-root component is opened without
following links, and the final directory identity is pinned for the process;
an ancestor link or later directory-chain substitution fails closed before
read, lock, or atomic replacement. Approval admission reserves the exact count
and encoded-byte capacity needed to turn every pending request into a maximum
typed approval and then append its maximum typed revocation. Both grant and
rollback therefore remain possible at the declared ledger boundary. The
approval ledger has its own independently replaced head manifest binding the
exact entry count, terminal entry hash, and current request-state set. Every
approval append first installs a generic durable intent binding the old head,
exact next entry, full next ledger image hash, and next head. Read-only
surfaces fail closed while that intent is present; the next controlled
mutation may finish only that exact precommitted generation. Unanchored
one-entry-ahead ledgers, prefix rollback after revocation, mismatched intents,
and replay of an intent against a later head are rejected.
Before a goal mutation writes its journal entry, the submission store reserves
the worst-case encoded bytes for the next independent journal anchor as well as
every pending terminal submission outcome. The submission lock remains held
through journal append and anchor convergence, so a near-capacity anchor cannot
fail after the goal generation has already committed.
Control Center approval preparation supplies the exact submission ref and
durably records the complete typed submission envelope before returning the
approval request. A lost prepare response or process restart can therefore
recover and retry the same request, idempotency ref, evidence ref, and
submission ref; React state is not the recovery authority. The aggregate
submission read model includes the exact authoritative approval request and
latest durable decision/grant envelope from that same locked approval
generation. This lets the UI recover an approval issued through CLI or after a
lost response without synthesizing a new decision or comparing presentation
reason text. A deny or revoke first resolves the exact linked pending
submission under the canonical approval, journal, then submission lock order;
only then is the terminal approval entry installed. A committed submission
wins exact reconciliation, while an uncommitted one cannot remain indefinitely
pending behind durable terminal approval truth. Aggregate reads also converge
expired pending approvals into a durable terminal `expired` decision and an
exact linked submission rejection before returning current state. The
submission store has an independent head binding its full state and rejection
anchor; every state change uses an exact write intent, so rollback, state loss,
or an unproven partial replacement fails closed while controlled recovery can
finish only the precommitted generation.
Completion verification and deterministic completion-event reconciliation use
the canonical approval, goal-journal, then run-event lock order. They validate
the exact approval generation, goal-journal approval binding, and every
retained or tombstoned event producer binding before consuming receipt evidence
or recreating a completion projection. The public service
exposes a read-only event facade; metadata event writes require one exact
request-scoped local approval, while receipt and completion events remain
trusted Core producer paths.

## Operator surfaces

- `GET /api/runtime/goals`
- `GET /api/runtime/goals/{goal_ref}`
- `POST /api/runtime/goals/approval-requests/create`
- `POST /api/runtime/goals/{goal_ref}/approval-requests/edit`
- `POST /api/runtime/goals/{goal_ref}/approval-requests/transition`
- `POST /api/runtime/goals/approval-requests/{approval_request_ref}/decision`
- `POST /api/runtime/goals/approval-requests/revoke`
- `POST /api/runtime/goals`
- `POST /api/runtime/goals/{goal_ref}/edit`
- `POST /api/runtime/goals/{goal_ref}/transition`
- `GET /api/runtime/run-events?run_ref=...&after_sequence=...&limit=...`
- `scripts/dev/uaa_runtime.py goals-list`
- `scripts/dev/uaa_runtime.py goal-show`
- `scripts/dev/uaa_runtime.py goal-approval-prepare`
- `scripts/dev/uaa_runtime.py goal-approval-decide`
- `scripts/dev/uaa_runtime.py goal-approval-revoke`
- `scripts/dev/uaa_runtime.py goal-create`
- `scripts/dev/uaa_runtime.py goal-edit`
- `scripts/dev/uaa_runtime.py goal-transition`
- `scripts/dev/uaa_runtime.py inspect-run-events`
- Control Center `/runtime` goal and durable-event summary

The exact-goal read and `goal-show` CLI return the bounded, content-free mutation
provenance chain alongside the current goal. Provenance includes operation,
version, idempotency, request fingerprint, approval, reason, and hash refs, but
does not repeat raw request payloads or goal text.

Every operator-facing goal mutation and public metadata-event append uses a
distinct two-step approval workflow. Preparation durably binds the exact
operation, subject, request fingerprint, idempotency identity, actor, and expiry
without authorizing or performing the mutation. A separate approve/deny
decision persists the request-scoped authority state; create, edit, transition,
and public metadata-event append then consume that exact approval under the
mutation claim. Trusted Core receipt/completion projection remains an internal
producer path rather than operator-minted authority. Revocation, expiry, denial,
drift, and fabricated refs fail closed. An already committed exact replay may
return its prior result after expiry or revocation only when the caller supplies
the original approval ref recorded in the durable journal.

Verified completion is currently blocked on the public API, CLI, and Control
Center because no trusted criterion-evaluator receipt producer exists in the
accepted runtime authority. Caller-supplied proof refs are not promoted into
evaluator authority. The read model exposes this blocked posture explicitly,
and `verify_completion` fails closed with
`GOAL_COMPLETION_TRUSTED_EVALUATOR_UNAVAILABLE`. The internal durable contract
retains the exact ordered criterion, proof, verifier, evaluator-receipt, source
goal-version, and completion-evidence bindings so a future separately
authorized trusted producer can use the same evidence model without changing
historical records.

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
Any ambiguous create, edit, or transition error marks the durable goal read as
stale and disables every goal mutation control. The separate read-only
`Refresh durable goal state` control must complete an authoritative
`GET /api/runtime/run-events` read before mutations become available again.
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
controlled worker-restart evidence, a second cancelled run, first-commit
failure at every genesis persistence boundary, unanchored-journal rejection,
precommitted event-generation repair, paired event/tombstone rollback
rejection, cross-store snapshot serialization, absolute-path
family rejection, criterion/cross-transaction provenance substitution, and
approval-ledger append-intent crash recovery for first and later generations,
unanchored approval-head rollback rejection, public-event producer
reclassification rejection, approval-bound completion reconciliation across
direct/runtime-projection/sync entry points, approval-prepare response-loss
restart recovery, safe-disabled committed-receipt replay, nonterminal aggregate
read non-initialization, quarantine-head and current-goal revalidation,
quarantine append-intent crash recovery and capacity exhaustion, no-follow
RuntimeGateway state-root admission and descriptor-exchange resistance through
ledger/safe-disable writes, reservation refresh immediately before dispatch,
canonical runtime-projection payload substitution rejection, self-attested
receipt rejection, and
behavioral UI mutation lockout until authoritative refresh. API and CLI
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
