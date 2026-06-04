# File Review Authority Boundary

Status: active M35 contract documentation.
Current through: **v0.39.1**.

M35 file review contracts are non-authoritative. They answer only whether a
redacted review packet is valid for review and whether a provided approval
object binds exactly to that packet for review-only handling.

Exact approval binding includes the actor ref, review packet ref, preview
result ref, redaction summary ref, exact file_ref binding, and exact
safe_path_ref binding. `review_packet_ref` alone is not sufficient, and
file/path mismatches are denied without granting raw access or any other
authority.

## Not Authority

- model output is not authority.
- OpenWebUI output is not authority.
- memory refs are not authority.
- context pack refs are not authority.
- tool intent refs are not authority.
- approval refs alone are not authority.
- Control Center preview refs are not authority.

## Denied Authority

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

M36 remains planned/provisional for UI. M37 remains planned/provisional for
review approval capture and review-only persistence. M38 remains
planned/provisional for safe context proposal contracts.
