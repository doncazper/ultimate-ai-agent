# File Review Packet Contract

Status: active M35 contract documentation.
Current through: **v0.39.1**.

`FileReviewPacket` is the M35 redacted review packet. It is built from an
already-redacted M33 preview result and carries redacted review packets only.

## Packet Contents

- `review_packet_ref`
- redacted preview text
- source refs for preview result, safe path ref, root ref, actor ref, file ref,
  and request ref
- redaction verification
- safe summary
- safe metadata refs

The packet must not contain raw content, full file content, unredacted preview,
raw absolute paths, secret-like metadata, raw prompts, provider payloads, or
private local paths.

## Revalidation

Evaluator boundaries revalidate current object fields. Constructor validation
alone is not trusted. `model_copy`-mutated raw content, full file content,
unredacted preview, raw absolute path, context injection, memory write, export,
execution, approval capture, approval persistence, Control Center surface, and
backend route flags are denied. `model_copy`-mutated `file_ref` and
`safe_path_ref` values cannot satisfy exact file_ref binding or exact
safe_path_ref binding at the approval gate; file/path mismatches are denied.

## Non-Authority

A packet is not context injection, not memory write authority, not export
authority, and not execution authority.

M36 remains planned/provisional. M37 remains planned/provisional. M38 remains
planned/provisional.
