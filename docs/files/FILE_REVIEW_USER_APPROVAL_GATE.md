# File Review User Approval Gate

Status: active M35 contract documentation.
Current through: **v0.39.1**.

`UserFileReviewApproval` is contract-only in M35. It is not captured through a
Control Center UI and is not persisted by M35.

The approval gate requires exact approval binding:

- actor ref must match.
- review packet ref must match exactly.
- preview result ref must match exactly.
- redaction summary ref must match exactly.
- file ref must match exactly through exact file_ref binding.
- safe path ref must match exactly through exact safe_path_ref binding.
- `review_packet_ref` alone is not sufficient; file/path mismatches are denied.
- Plain-text verifier phrase: review_packet_ref alone is not sufficient.
- expired approvals are denied.
- revoked approvals are denied.
- replayed approvals are denied when replay evidence is present.
- `approval_ref` alone is not authority.
- `approval_test_*` is not runtime authority.

An allowed decision is review-only. It does not grant raw file access, context
proposal, context injection, memory writes, export, execution, tool execution,
or backend mutation authority.

M36 remains planned/provisional. M37 remains planned/provisional. M38 remains
planned/provisional.
