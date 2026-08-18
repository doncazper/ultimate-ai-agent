# Review Convergence Policy

Status: active engineering-process policy. This document grants no runtime,
network, browser, provider, model, shell, connector, merge, or release
authority.

This policy reduces avoidable review and CI churn without lowering UAA's
acceptance bar. Exact-head CI and review, policy and approval enforcement,
redaction, OpenAPI, Foundation Gate, dependency ordering, and proportional
post-merge confirmation remain mandatory.

The active operator record is
[`issue #341`](https://github.com/doncazper/ultimate-ai-agent/issues/341#issuecomment-5113957680).
This repository document is the stable implementation guide for that cadence.

## Choose A Convergent Review Unit

A pull request should own one durable contract, one authority boundary, or one
independently reviewable product slice. Split work when persistence, runtime
authority, API contracts, and user-interface behavior can be reviewed
independently without creating a temporarily unsafe state.

Keep a cross-surface slice together only when splitting it would break a
required CLI/Core/API/Control Center contract or leave an intermediate commit
with inaccurate authority or product truth. Record that reason in the pull
request.

Do not expand a feature pull request to absorb a newly discovered architectural
prerequisite. Extract the smallest isolated prerequisite when either condition
is met:

- the same structural proof class recurs after a repair; or
- two exact-head review rounds introduce new architectural findings.

An already-running atomic unit does not need to be destructively split merely
to satisfy this policy. Apply the structural repair to its next candidate when
that remains the smaller and safer closeout.

## Record The Invariant Matrix Before Coding

Mark each row applicable, not applicable, or blocked, and identify the owning
test or evidence. A blank row is not evidence that the invariant is irrelevant.

| Invariant class | Required questions |
|---|---|
| Authority and provenance | What trusted producer owns the claim? What exact scope, approval, receipt, and policy decision are bound? Can caller-supplied safe-shaped data substitute for trusted evidence? |
| Atomicity and recovery | What happens at every persistence boundary? Are first-write, one-generation-ahead, retry, cancellation, and rollback states deterministic and fail closed? |
| Concurrency and generations | Can a reader mix generations? Is lock order explicit? Can first lock creation, timeout, cancellation, or process death strand capacity or state? |
| Tampering and substitution | Are every field, ordering, arity, cross-operation, cross-transaction, and recomputed-wrapper-hash substitutions rejected? |
| Capacity and retention | Do encoded UTF-8 bytes, record counts, proof arity, reservations, tombstones, eviction, and maximum-schema envelopes derive from the same typed limits? |
| Failure truth | Can the operator distinguish not started, committed, rejected, ambiguous, and projection-failed outcomes without raw data or false completion claims? |
| Cross-surface parity | Do Python Core, CLI, API/OpenAPI, manifest, and Control Center use the same grammar, bounds, authority posture, and durable truth where applicable? |

Persistence-heavy or proof-bearing changes should convert applicable rows into
table-driven tests rather than a sequence of field-specific patches.

## Verification And Review Cadence

1. Reconcile exact `main`, the branch head, active checks, reviews, and
   unresolved threads. Do not duplicate work owned by another isolated lane.
2. Perform a read-only design and provenance preflight against the complete
   changed contract.
3. Implement with focused tests and targeted checks. Batch all known findings.
4. Before publishing, perform one structural adversarial audit using the
   invariant matrix. Repair the abstraction when a finding represents missing
   provenance, atomicity, recovery, canonical encoding, or contract ownership.
5. Run one broad local qualification on the final candidate. If the candidate
   changes afterward, rerun only the proportional affected checks and one new
   broad final qualification.
6. Publish once per final candidate. Request one exact-head CI and review cycle.
   Do not trigger duplicate hosted runs or concurrent review requests for the
   same head.
7. If exact-head review finds defects, batch the complete set before the next
   candidate. Do not resolve current or historical actionable threads until the
   replacement exact head is clean.
8. After a clean exact head, reply to and resolve threads as one audited
   closeout, merge under the existing policy, verify exact `main`
   proportionally, and clean only the lane-owned branch and worktree.

Generated evidence should be refreshed only after implementation stabilizes.
Review the generated change as a bounded provenance delta; do not hand-edit
scores, weaken drift checks, or mix unrelated generated output into the lane.

## Review-Ready Gate

A candidate is review-ready only when:

- the pull request names its single contract or authority boundary;
- applicable invariant-matrix rows have tests or explicit blocked evidence;
- the complete diff has received a structural adversarial audit;
- focused checks and the one broad final qualification are recorded;
- generated evidence, if any, is an expected bounded delta;
- no duplicate CI or review request is active for the exact head; and
- safety, authority, redaction, API, Foundation Gate, and product-language
  requirements remain unchanged.

This cadence optimizes preparation and review-unit size. It never permits
merging around a failure, accepting unresolved actionable findings, weakening
assertions, or converting planning evidence into runtime authority.
