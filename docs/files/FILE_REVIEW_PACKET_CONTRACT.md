# File Review Packet Contract

Status: active M35 contract documentation.
Current through: **v0.39.0**.

`FileReviewPacket` is the M35 redacted review packet. It is built from an
already-redacted M33 preview result and carries redacted review packets only.

## Packet Contents

- `review_packet_ref`
- redacted preview text
- source refs for preview result, safe path ref, root ref, actor ref, and
  request ref
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
backend route flags are denied.

## Non-Authority

A packet is not context injection, not memory write authority, not export
authority, and not execution authority.

M36 remains planned/provisional. M37 remains planned/provisional. M38 remains
planned/provisional.
