# Context Handoff Approval

Status: active M40 contract documentation.
Release: **v0.44.0 / M40 - Context Handoff Approval, No Injection**.

M40 adds Context Handoff Approval contracts for deciding whether a previously
approved, safe context proposal may proceed to future handoff review. The
approval is review-only. It is not context injection, not OpenWebUI handoff
execution, not model authority, not memory authority, not export authority, and
not execution authority.

## Contract Shape

The M40 contract accepts a safe context proposal and a
`ContextHandoffApprovalRequest`. The request must carry exact proposal binding
refs:

- `approval_ref`
- `actor_ref`
- `proposal_ref`
- `approval_record_ref`
- `review_packet_ref`
- `preview_result_ref`
- `redaction_summary_ref`
- `file_ref`
- `safe_path_ref`
- `idempotency_key`

The evaluator returns a `ContextHandoffApprovalDecision`. A valid approval may
set `handoff_approved_for_review=True`, but every authority and performed flag
remains false.

## Required Denials

- approval_ref alone is not authority.
- approval_test_ is not runtime authority.
- mismatched proposal, actor, approval record, review packet, preview result,
  redaction summary, file, or path refs are denied.
- expired, revoked, and replayed approvals are denied.
- context injection is denied.
- OpenWebUI handoff execution is denied.
- model calls are denied.
- memory writes are denied.
- export is denied.
- execution is denied.
- raw file access and raw content are denied.

Evaluator boundaries revalidate the current object fields before allowing a
review-only handoff approval decision. Constructor validation alone is not
trusted, so `model_copy` mutations to proposal or request authority fields are
denied.

M41 remains future.
