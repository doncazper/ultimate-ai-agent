# File Review Approval Capture

Status: active M37 contract documentation.
Release: v0.41.0 / M37 - Review Approval Capture, Review-Only Persistence.

M37 adds review approval capture for already-redacted file review packets. The
capture is review-only persistence: it records whether a reviewer approved or
denied a specific redacted review packet for review purposes only.

The capture request must bind exactly to:

- `review_packet_ref`
- `preview_result_ref`
- `redaction_summary_ref`
- `file_ref`
- `safe_path_ref`
- `actor_ref`

The capture decision stores safe refs only. It does not store raw content,
full-file content, unredacted preview, raw absolute paths, private paths, prompt
payloads, provider payloads, credentials, cookies, or secret-like values.

Review approval capture does not grant raw file access, context proposal,
context injection, memory writes, export, execution, tool authority, production
authority, or approval refs as authority. `approval_ref` alone is not authority,
and `approval_test_` refs are denied.

M37 guarantees no raw file access, no context proposal, no context injection,
no memory write, no export, and no execution from review approval capture.

M38 remains planned/provisional.
