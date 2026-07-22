# Phase 05: Action Inbox, Work Board, And Session UX

Coverage: O05, O07, B12, L05, L09, and L15.

Objective: turn the already governed Action Inbox and Work Board into a mature,
conflict-safe founder/operator workflow while improving sessions without moving
truth into React.

## Fresh Delta Gate

Re-inventory Action Inbox, approval queue, Work Board, Chat, session catalog,
north-star UI, and any in-flight frontend PR. Preserve current backend-owned
decision and board receipts. Do not create a second board or session store.

## Action Inbox Outcomes

1. For every action, show exact requested scope, resources, side-effect class,
   risk, approval expiry, current policy result, evidence, expected receipt,
   rollback/safe-disable posture, and whether execution has started.
2. Make approve, edit, reject, defer, cancel, and inspect receipt coherent and
   keyboard accessible.
3. Prevent stale approvals: any edit to scope, resource, payload fingerprint,
   route, adapter, deadline, or authority inputs invalidates the old decision.
4. Add the missing dedicated CLI inspection path for the approval queue.
5. Refresh from backend after every mutation and show conflicts explicitly.

## Work Board Outcomes

1. Add backend revision/version to board snapshots and mutation preconditions.
2. Reconcile live or polled backend changes without overwriting local drag
   presentation state or another accepted mutation.
3. Persist reorder/create/task changes only after the backend receipt succeeds.
4. On conflict, reload authoritative state, explain the conflict, and offer a
   new proposal instead of silently replaying stale intent.
5. Preserve approval, idempotency, receipt, rollback, CLI/API, and Evidence
   linkage for every board mutation.

## Session UX Outcomes

Add backend-owned titles, search/filter, unread/read state, archive, and
restoration before considering split panes. Forking or duplication must create
explicit lineage. UI-only layout preferences may stay local; session existence,
goal, state, and evidence may not.

Autosave is allowed only for presentation preferences or separately accepted
exact settings lanes. Backend settings mutations require validation, version
precondition, receipt, refresh, and safe failure.

## End-To-End Acceptance

- Approve/edit/reject/defer real local Action Inbox records and prove receipts.
- Open the same Work Board in two clients, create a revision conflict, and prove
  no lost update or false completion.
- Reload after card reorder and session archive and prove backend persistence.
- Stop the backend during a mutation and prove the UI remains uncommitted and
  truthful.
- Verify keyboard, reduced-motion, responsive, and screen-reader behavior.

Commit message:

```text
feat(control-center): harden actions board and session workflows
```
