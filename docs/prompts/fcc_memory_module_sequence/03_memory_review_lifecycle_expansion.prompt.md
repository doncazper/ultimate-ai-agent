# Real Review Lifecycle Expansion

Goal: keep accept/correct/reject and add backend receipt models for `defer`,
`merge`, `supersede`, and `forget_request`.

Scope:
- Add POST routes for the new lifecycle decisions.
- Extend idempotency replay/conflict behavior.
- Record safe receipt refs for every decision.
- `forget_request` records posture only. It must not delete, export, or mutate
  underlying recall records.
- Merge/supersede receipts mark old candidates/records as superseded posture,
  with no silent deletion.

Boundaries:
- No delete/export execution.
- No context injection or automatic recall.
- No connector writes or model/provider calls.

Verification:
- Tests for defer, merge, supersede, forget_request, replay, conflict, and
  authority-denial flags.
- Evidence Timeline memory decision answers updated by prompt 11.
