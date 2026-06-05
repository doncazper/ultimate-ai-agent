# Context Handoff Receipt Plan

Status: active M40 receipt-plan documentation.
Release: **v0.44.0 / M40 - Context Handoff Approval, No Injection**.

The M40 receipt plan stores safe refs only. It records enough metadata to audit
that a review-only context handoff approval decision was evaluated, but it does
not store raw content and does not become authority.

## Stored Refs

- `receipt_plan_ref`
- `approval_ref`
- `proposal_ref`
- `approval_record_ref`
- `review_packet_ref`
- `preview_result_ref`
- `redaction_summary_ref`
- `file_ref`
- `safe_path_ref`
- `actor_ref`

## Never Stored Or Performed

- no raw content.
- no full-file content.
- no unredacted preview.
- no raw absolute path.
- no context injection.
- no OpenWebUI handoff execution.
- no model calls.
- no memory writes.
- no export.
- no execution.

The receipt is non-authoritative. It cannot be used as a context pack,
injection approval, memory write approval, export approval, execution approval,
or production authority.

M41 remains future.
