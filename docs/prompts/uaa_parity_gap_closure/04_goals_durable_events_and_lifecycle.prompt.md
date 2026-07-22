# Phase 04: Goals, Durable Events, And Run Lifecycle

Coverage: H01, H02, O01, O03, P07, B04, B06, B13, L06, L07, and L10.

Objective: provide a persistent founder/operator goal lifecycle and truthful
durable run progress with interruption, replay, cancellation, approval wait,
restart, and proof-backed completion.

## Fresh Delta Gate

Re-inventory current goal, plan, mission, durable worker, streaming-progress,
run-event, approval-wait, and orchestration implementations. A deterministic
sample-event builder or route describing unsupported live SSE does not count as
durable event implementation.

## Persistent Goal Outcomes

1. Store goals in Python Core with stable safe ref, bounded objective, outcome,
   success criteria, constraints, in-scope resources, stop condition, state,
   budget, version, created/updated times, and evidence refs.
2. Support create, inspect, edit, pause, resume, block, wait, cancel, and clear.
3. Separate `complete_requested` from `verified_complete`. Only deterministic
   verifier/receipt evidence can produce verified completion. Model output may
   suggest a state but never changes it authoritatively.
4. Link goals to Plans, runs, Action Inbox items, Work Board cards, and Evidence
   without duplicating durable truth.
5. Provide CLI/API/OpenAPI/manifest/Control Center parity and version-conflict
   handling.

## Durable Event Outcomes

1. Replace preview/sample replay with a real durable event source for accepted
   local run types.
2. Use monotonic sequence, stable event ref, run ref, timestamp, kind, redacted
   summary, proof/receipt refs, predecessor/hash integrity, and bounded retention.
3. Support cursor-based replay and reconnect without duplication. Gaps,
   corruption, stale cursor, unknown run, and retention loss must be explicit.
4. Add a read-only live transport only when its exact streaming authority lane
   is accepted. Read transport cannot accept control messages.
5. Place stop, retry, resume, and approval decisions on separate exact routes
   that re-evaluate authority immediately before action.
6. Apply bounded queues and backpressure. Slow clients must not cause unbounded
   memory, reorder events, or block authoritative receipt persistence.

## Lifecycle Hardening

- cancellation before start, during adapter start, after side effect, before
  receipt, and during receipt commit;
- approval wait expiry, reject, edit, resume, and restart;
- stale claims, orphaned workers, duplicate worker identity, dead letters, and
  restart admission fences;
- terminal failure versus retryable failure classification;
- no late success event after cancellation unless the receipt proves a side
  effect already completed; and
- no completion from stale or unverified evidence.

## End-To-End Acceptance

Run a real accepted local mission from goal creation through plan, run events,
approval wait, allowed action or read task, receipt, Evidence, and verified goal
completion. Disconnect and reconnect the client, restart the worker at a
controlled point, and cancel a second run. Prove identical state through CLI,
API, and Control Center after process restart.

Test arbitrary UTF-8 splits, duplicate/gap/reordered sequences, cross-chunk
redaction, slow consumers, cursor resume, and bounded retention.

Commit message:

```text
feat(runtime): add proof-backed goals and durable run events
```
