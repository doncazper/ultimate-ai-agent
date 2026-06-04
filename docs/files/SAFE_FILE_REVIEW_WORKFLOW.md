# Safe File Review Workflow

Status: active M35 contract documentation.
Current through: **v0.39.0**.

v0.39.0 / M35 implements Safe File Review Workflow Contracts. The workflow is
contract-only and review-only: it can package an already-redacted file preview
result into a redacted review packet and evaluate whether an exact approval
object applies to that exact packet for review-only handling.

M35 does not read files. It consumes the existing M33 redacted file preview
result contract. M35 adds no Control Center UI, no approval capture, no approval
persistence, no context proposal, no context injection, no memory writes, no
export, no execution, no backend routes, and no production authority.

## Workflow

1. A governed M33 redacted preview result exists.
2. `FileReviewRequest` identifies the actor, request, and preview result ref.
3. `FileReviewPacket` stores redacted review packets only.
4. `FileReviewRedactionVerification` records that redaction summary and
   redaction verification exist.
5. `FileReviewGate` checks exact approval binding against the packet refs.
6. `FileReviewDecision` returns review-only decisions.
7. `FileReviewReceiptPlan` stores refs only and is not authority.

## Required Boundaries

- no raw file access.
- no raw content.
- no full-file reads.
- no unredacted preview.
- no approval capture.
- no approval persistence.
- no context proposal.
- no context injection.
- no memory writes.
- no export.
- no execution.
- no backend routes.

M36 remains planned/provisional as CCC File Review Surface, Review-Only. M37
remains planned/provisional as Review Approval Capture, Review-Only Persistence.
M38 remains planned/provisional as Safe Context Proposal From Approved Review.
