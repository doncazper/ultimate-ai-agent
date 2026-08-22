# Autocorrect Controls Recovery Contract

Status: triage-ready recovery source. It grants no automatic correction or
unreviewed mutation authority.

Detailed reconstructed plan:
`docs/implementation/UAA_AUTOCORRECT_CONTROLS_IMPLEMENTATION_PLAN.md`.

Vision status: medium-confidence conservative reconstruction. No exact archived
prompt was located. Queue completion covers the bounded proposal/ChangeSet
slice only, not arbitrary or silent cross-UAA autocorrection.

## Outcome

Provide reviewable correction proposals, exact diffs, confidence and evidence
truth, rejection learning, rollback, and safe-disable controls across UAA
operator workflows.

## In Scope

- Proposal-only correction contracts and bounded comparison views.
- Approval, idempotency, revision, rollback, and evidence receipts.
- Explicit correction outcomes for accepted, rejected, superseded, stale, and
  blocked states.

## Out Of Scope

- Silent edits, automatic prompt or memory rewriting, connector writes,
  unrestricted file mutation, or model output as authority.

## Acceptance

- No correction mutates canonical state without the exact approved child lane.
- Stale revisions and changed payloads fail closed.
- Redaction, rollback, CLI/API parity, and focused regression evidence are
  required before promotion.
