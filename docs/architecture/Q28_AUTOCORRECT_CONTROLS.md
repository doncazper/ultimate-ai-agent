# Q28 Autocorrect Controls

Status: implemented proposal-only baseline. This contract grants no automatic
correction, canonical mutation, ChangeSet creation, approval, rollback
execution, model call, connector write, or production authority.

## Purpose

Q28 turns an already-normalized correction candidate into a reviewable,
content-free comparison. It binds the proposal to one existing ECO-008 target,
its exact revision, typed field-diff fingerprints, evidence refs, confidence,
and any prior rejection-learning refs. Raw before/after values are not accepted
or returned.

The supported targets are exactly the existing local ECO-008 adapters:

- task and task occurrence;
- board and board template;
- calendar set.

Person, CRM, inbox, file, memory, create/delete, lifecycle, connector, and
external targets remain out of scope until their own exact ChangeSet adapters
and authority lanes are accepted.

## Review flow

1. `CorrectionProposalRequest` supplies safe refs and one to sixteen ECO-008
   `FieldDiff` records.
2. `build_correction_proposal` derives stable proposal, comparison,
   review-packet, proposed ChangeSet, approval-scope, and rollback-plan refs.
3. A mismatched exact revision becomes `stale`. Safe-disable and confidence
   below 60 become blocked states. None can be accepted for ChangeSet review.
4. `CorrectionReviewSession` records a process-local review outcome for
   accept, reject, or supersede. Acceptance means only
   `accepted_for_changeset_review`; it does not create or apply a ChangeSet.
5. Reject and supersede produce content-free learning refs. They do not rewrite
   prompts, memory, canonical records, or assertions.

The process-local review session is capped at 256 receipts and fails closed when
full. It gives API and CLI review previews same-process idempotency and
changed-payload conflict detection, but it is not a durable receipt store.
Restarting the process clears the replay guard. Durable review history requires
a later exact local persistence lane.

## Failure and rollback posture

- A stale current revision fails closed and instructs the caller to refresh.
- Reusing an idempotency ref with changed proposal or decision material raises
  `AUTOCORRECT_IDEMPOTENCY_PAYLOAD_CONFLICT`.
- Changing the reviewed proposal or fingerprint raises
  `AUTOCORRECT_PROPOSAL_BINDING_CHANGED`.
- Reaching the process-local receipt cap raises
  `AUTOCORRECT_REVIEW_SESSION_CAPACITY_REACHED`; the service does not evict an
  earlier binding and silently weaken conflict detection.
- Every accepted review identifies the expected separately governed ECO-008
  ChangeSet and approval-scope refs.
- The rollback plan is readiness metadata only. A rollback receipt can exist
  only after an exact ChangeSet was applied by ECO-008; Q28 performs neither
  action.
- Safe-disable blocks review and leaves no canonical state to undo.

## Surfaces

Python Core:
`src/ultimate_ai_agent/core/ecosystem/corrections.py`

Protected local API:

- `GET /control-center/autocorrect/status`
- `POST /control-center/autocorrect/proposals/preview`
- `POST /control-center/autocorrect/reviews/preview`

Both POST routes are validation-only. The review route maintains only the
bounded process-local replay guard described above.

Repo-local CLI:

```bash
PYTHONPATH=src .venv/bin/python scripts/inspect_autocorrect_controls.py status
PYTHONPATH=src .venv/bin/python scripts/inspect_autocorrect_controls.py proposal
PYTHONPATH=src .venv/bin/python scripts/inspect_autocorrect_controls.py review --decision accept
PYTHONPATH=src .venv/bin/python scripts/inspect_autocorrect_controls.py proposal --stale
```

The CLI uses fixed synthetic safe refs and has no file/source input option.

## Explicit non-authority

Q28 provides no canonical mutation, no ChangeSet creation, no approval grant,
no rollback execution, no source read, no model/provider call, no prompt or
memory rewrite, no connector/external write, no browser/shell/subprocess
runtime, no background autonomy, and no public or production readiness claim.
