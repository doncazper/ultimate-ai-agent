# Context Proposal Binding Display Policy

Status: active for **v0.43.0 / M39 - CCC Context Proposal Surface**.

M39 must display exact safe binding refs for every selected context proposal.
The binding display is review evidence only and is not authority.

Required refs:

- `context_proposal_ref` or `proposal_ref`.
- `approval_ref` or `approval_record_ref`.
- `review_packet_ref`.
- `preview_result_ref`.
- `redaction_summary_ref`.
- `file_ref`.
- `safe_path_ref` or `path_ref`.
- `actor_ref`.

The binding display must not reveal raw absolute paths. It must not allow a
caller-selected root, file picker, browser, upload, directory listing,
traversal, or arbitrary file read. It must not display raw content or
unredacted preview.

Binding refs can explain provenance. They cannot authorize context handoff,
context injection, OpenWebUI handoff, memory writes, export, execution, model
calls, raw file access, or approval mutation.

M40 remains future.
