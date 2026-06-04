# File Review Binding Display Policy

Status: active M36 documentation.
Current through: **v0.40.0**.

M36 displays exact binding refs for already-redacted review packets. The refs
are identifiers for human review and verifier evidence only. They are not
authority.

## Required Binding Refs

- `review_packet_ref`
- `preview_result_ref`
- `redaction_summary_ref`
- `file_ref`
- `safe_path_ref` / `path_ref`

The UI must keep these refs visibly tied to the selected redacted review
packet. It must not replace exact safe refs with raw absolute paths.

## Authority Boundary

Displayed refs do not authorize raw file access, approval capture, approval
persistence, context proposal, context injection, memory writes, export,
execution, tool use, or backend mutation.

M37 remains planned/provisional for review approval capture. M38 remains
planned/provisional for context proposal from approved review.
