# v0.39.1 README Import

Status: historical release packet.
Release: **v0.39.1 / M35 hardening - File Review Exact File/Path Binding**.

v0.39.1 hardens M35 Safe File Review Workflow Contracts. It requires exact
approval binding across actor, review packet, preview result, redaction
summary, `file_ref`, and `safe_path_ref`, and denies file/path mismatches at the
review gate.

This archived packet is historical evidence for the v0.39.1 release. Active
currentness is maintained by `VERSION.md`, `README.md`,
`docs/canonical/09_roadmap.md`, and `docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md`.

## Boundaries

- redacted review packets only.
- exact file_ref binding.
- exact safe_path_ref binding.
- `review_packet_ref` alone is not sufficient.
- file/path mismatches are denied.
- review-only decisions.
- no raw file access.
- no raw content.
- no approval capture.
- no approval persistence.
- no context proposal.
- no context injection.
- no memory writes.
- no export.
- no execution.
- no backend routes.

M36 remains planned/provisional. M37 remains planned/provisional. M38 remains
planned/provisional.
