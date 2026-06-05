# CCC Context Proposal Surface

Status: active for **v0.43.0 / M39 - CCC Context Proposal Surface**.

M39 adds a read-only Control Center surface for M38 Safe Context Proposal From
Approved Review objects. The surface is proposal-only, mock and non-authoritative,
and exists so a human can inspect safe proposal summaries,
approved-review provenance, exact binding refs, redaction verification, safe
proposal sections, decision status, and receipt-plan metadata.

The route is `/context/proposals`. It is a frontend-only CCC surface and adds
no backend route.

## Required Display

The surface displays safe refs only:

- `context_proposal_ref` / `proposal_ref`.
- `approval_ref` / `approval_record_ref`.
- `review_packet_ref`.
- `preview_result_ref`.
- `redaction_summary_ref`.
- `file_ref`.
- `safe_path_ref` / `path_ref`.
- `actor_ref`.

It also displays source chain refs, redaction verification status, safe proposal
sections, proposal-only decision state, approval-gate contract status, and
receipt-plan metadata.

## Boundary

The M39 surface is not context handoff. It is not context injection. It is not
OpenWebUI handoff. It does not write memory. It does not export. It does not
execute. It does not call models or providers. It does not grant raw file
access. It does not display raw file content, full-file content, unredacted
preview, raw absolute paths, or secret-like values.

M39 adds no approve, deny, submit, save, mark-reviewed, handoff, inject,
export, download, copy-raw, memory write, run, execute, model-call, file picker,
browser, upload, or root selector controls.

M40 remains future.
