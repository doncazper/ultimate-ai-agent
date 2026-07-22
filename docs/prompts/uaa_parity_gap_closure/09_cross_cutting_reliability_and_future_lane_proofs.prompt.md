# Phase 09: Cross-Cutting Reliability And Future-Lane Proofs

Coverage: O06, P05, P06, B01-B14, including the cross-cutting portions already
addressed in Phases 02-08.

Objective: close the adversarial bug classes suggested by Hermes/OpenClaw and
prove that any future provider or connector lane cannot graduate without
exactly-once, retry, cancellation, redaction, and approval correctness.

## Fresh Regression Inventory

Re-read all Phase 02-08 merges and re-run the convergence ledger. For each B ID,
locate the production boundary and at least one meaningful regression test.
Do not satisfy this phase with a checklist document alone.

## Approval And Adapter Safety

- prove owner/requester/resource/action/payload/route/adapter/deadline binding;
- deny before adapter start when approval infrastructure is missing, stale,
  expired, mismatched, unavailable, or throws;
- prove cloned approval refs and changed dispatch identities cannot replay; and
- require every new mutating adapter to register fail-closed negative tests.

## Lifecycle And State Safety

- test restart/admission fences at pre-start, claimed, started, approval wait,
  side-effect-unknown, receipt commit, and terminal states;
- prove cancellation and shutdown clean timers, locks, processes, tasks,
  connections, queues, and watchers;
- prove approval wait expiry cannot dispatch and orphan recovery cannot double
  start; and
- prevent stale UI, stale receipts, or optimistic completion from replacing
  newer authoritative state.

## Streaming, Path, And Redaction Safety

- arbitrary UTF-8 and surrogate splits, duplicate/gap/reorder, reconnect, and
  backpressure tests;
- stateful cross-chunk redaction for every live/log/event stream;
- export/backup/restore traversal, symlink, hardlink, special-file, archive-bomb,
  and collision tests; and
- bounded error bodies and redacted diagnostics with no raw payload persistence.

## Provider And Connector Promotion Proof Floor

Do not activate provider or connector authority unless separately accepted.
However, implement the real shared production invariants that any later adapter
must use; do not create a disconnected planning-only contract:

1. A delivery-attempt state machine with stable nonce/idempotency ref, pending,
   committed, failed-before-send, partial, unknown-outcome, reconciled, and
   terminal states.
2. Durable delivery evidence that prevents automatic retry after a visible or
   possibly visible send.
3. Retry classification separating safe reads, idempotent mutations,
   non-idempotent mutations, ambiguous side effects, auth failures, rate limits,
   and permanent errors.
4. A single-flight invocation guard preventing duplicate provider/model/image
   calls for one logical request.
5. Abort/deadline propagation through credential resolution, rate-limit wait,
   network/read adapter, parsing, tool execution, and receipt commit.
6. Exact requester-scoped adapter resolution; shared-thread or shared-session
   state must not inherit another requester's authority.

These invariants must be wired into current accepted local adapters where
applicable and covered by integration tests. A fake production provider or
connector may not be used to claim live external parity.

## End-To-End Fault Matrix

Exercise at least: missing approval service, wrong scope, replay, cancellation
race, restart during start, retry after unknown outcome, duplicated event,
UTF-8 split, secret split, slow client, stale UI response, storage budget
exhaustion, corrupted backup, memory-write conflict, and stale proof.

Commit message:

```text
fix(runtime): close parity reliability and replay gaps
```
