# CCC File Review Surface

Status: active M36 documentation.
Current through: **v0.40.0**.

v0.40.0 / M36 implements the CCC File Review Surface, Review-Only. The
surface displays redacted file review packets that were already produced by
M35 contracts. It is a Control Center display surface only.

## Display Contract

The surface may display:

- redacted preview.
- redaction summary.
- exact binding refs:
  - `review_packet_ref`
  - `preview_result_ref`
  - `redaction_summary_ref`
  - `file_ref`
  - `safe_path_ref` / `path_ref`
- review-only decision status.
- approval gate contract status.
- receipt plan metadata.
- visibly mock and non-authoritative fallback data.

## Safety Boundary

- review-only.
- mock and non-authoritative when fallback data is shown.
- redacted review packets only.
- no approval capture.
- no approval persistence.
- no raw file access.
- no raw file display.
- no raw file content storage.
- no full-file reads.
- no file picker, browser, upload, or root selector.
- no export, download, or copy-raw controls.
- no context proposal.
- no context injection.
- no memory writes.
- no execution or tool controls.
- no backend routes.
- no dependencies.

M37 remains planned/provisional for Review Approval Capture, Review-Only
Persistence. M38 remains planned/provisional for Safe Context Proposal From
Approved Review.
