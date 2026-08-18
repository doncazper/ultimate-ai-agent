# Delegated Mission And Document Organization Recovery Contract

Status: triage-ready recovery source. It grants no automatic delegation,
filesystem mutation, or document authority.

## Outcome

Make delegated missions and document organization durable, inspectable, and
reviewable across Today, Plans, Work Board, Evidence, and Memory without
placing workflow truth in React state.

## In Scope

- Canonical mission, artifact, handoff, provenance, and organization contracts.
- Read models, CLI inspection, safe refs, and deterministic review flows.
- Explicit recovery, idempotency, and no-silent-stall evidence.

## Out Of Scope

- Unscoped file moves, connector writes, hidden memory writes, or automatic
  task execution.
- Raw document content in durable evidence.

## Acceptance

- One canonical owner exists for every mission and document artifact state.
- Delegation and organization decisions are receipt-backed and reversible.
- Focused Python, API, CLI, documentation, and Control Center tests pass for
  the accepted child scope.
