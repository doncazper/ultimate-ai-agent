# TAW-05 Outcome Evidence And Governed Improvement

Status: bounded founder-private-dogfood implementation evidence. This slice
adds a pure Python Core projection over immutable safe-ref evidence. It does
not add a receipt-arrival handler, durable statistics mutation, runtime tool
execution, model/provider call, ordinary-chat call, connector, external write,
online training, automatic policy or alias promotion, or authority.

Acceptance-state role: `non-owner`. This slice records bounded implementation
evidence only. Mutable founder-private acceptance state is owned by the
content-addressed TAW-08 report and its two bounded active-truth reconciliations;
independent promotion is a separate gate.

## Contract

TAW-05 binds every observation to a versioned capability contract, exact TAW-01
operation-schema fingerprint, reviewed policy snapshot, evaluator revision,
reviewed completion SLA, clock source, safe environment class, durable start
fingerprint, and—when present—one immutable terminal receipt. The reviewed SLA
is the projection window and cannot exceed the repository hard maximum.

Terminal receipts use the closed status set `succeeded`, `failed`, `canceled`,
and `rolled_back` through a Python 3.10-compatible string enum. Exact start and
receipt replays are deduplicated before projection. Reusing an attempt,
durable-start ref, or receipt identity with conflicting fingerprints—or
deserializing a projection with duplicate observation identities—invalidates
the projection. A terminal receipt without its exact bound start and governing
contract, a status/ref pair outside that contract's closed map, or evidence
outside the as-of census also fails closed.

## Recomputable Census

`project_capability_outcomes` is a deterministic, non-authoritative function.
It accepts bounded immutable starts and receipts and emits a complete as-of
census:

- terminal outcomes are included in the health, reliability, and familiarity
  denominators;
- canceled and rolled-back outcomes are adverse non-successes;
- a started attempt still inside the reviewed window remains `still_live` and
  is excluded from those denominators;
- a started attempt beyond the window with no receipt becomes
  `unresolved_overdue`, remains `outcome_uncertain`, and is included as a
  non-success; and
- proposal or approval records without a durable execution start retain their
  ordinary canonical lifecycle posture.

Counts are rederived from the observation tuple during validation, reconciled
against the published census, and bound into one canonical projection
fingerprint. A caller cannot repair contradictory counts merely by recomputing
the outer fingerprint. The projection records the as-of time, window, clock,
inventory, terminal split, live/overdue counts, denominators, and integer
success basis points.

Prior projections never supply counts or authority. A matching prior is only
reported as current non-authoritative evidence. Its exact policy fingerprint,
contract, operation-schema, policy snapshot, and evaluator revision bindings
must remain current; any mismatch marks it stale and invalidated.

## Operator Corrections

Correction input is safe-ref-only and forbids additional raw fields. A
correction can become only `eligible_for_separate_durable_promotion` when it has
a synthetic or fully redacted fixture ref, accepted independent-review ref,
and passing content-safety receipt ref. The decision writes no fixture and
performs no promotion. Untransformed, unreviewed, rejected, or safety-unverified
corrections remain blocked. Each decision is fingerprint-bound to the complete
validated correction evidence, so reusing a correction ref cannot rebind a
decision to different fixture, review, or safety evidence.

## Inspection Boundary

This slice exposes importable Python Core contracts and a repo-local verifier.
It adds no API route, CLI product command, Control Center surface, runtime
wiring, or model-visible context. TAW-06 remains responsible for operator
diagnostic surfaces consuming this same backend read model.

## Verification

Run:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_tool_aware_cognition_taw05.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_aware_cognition_taw05.py
```

The focused suite covers the full terminal/live/overdue census, denominator
rules, exact replay dedupe, deserialized duplicate rejection, conflicting
identity reuse, orphan and cross-bound receipts, terminal status-map binding,
timestamp and environment binding, reviewed-window bounds, Python 3.10 enum
compatibility, bounded iterables, exact-policy stale priors, lifecycle posture,
correction-evidence binding, safe correction promotion eligibility, raw-field
rejection, count recomputation, and all zero-authority invariants.

## Next Slice

TAW-06 may add human-readable CLI and API diagnostics only through a shared,
redacted, bounded Python Core read model with OpenAPI, API-manifest,
side-effect-classification, and parity proof. TAW-05 does not complete Q22 and
does not own mutable founder-private acceptance state.
