# Mobile Review Approval Capture

v0.53.0 / M49 implements Mobile Review Approval Capture as core Python
contracts for exact-scope, review-only mobile approval records.

Mobile review approval capture records that a user reviewed a redacted mobile
review packet and selected an approve-review-only or deny-review-only decision.
It is safe refs only: approval ref, actor ref, mobile surface ref,
review_packet_ref, preview_result_ref, redaction_summary_ref, file_ref,
safe_path_ref, idempotency key, and receipt plan ref.

M49 approval capture is exact-scope, actor-bound, resource-bound,
replay-safe, non-transferable, and revocable. The actor, mobile surface,
review packet, preview result, redaction summary, file ref, and safe path ref
must match the expected refs exactly before a record can be captured.

The M49 capture result is review-only and non-authoritative. It grants no raw
file access, no raw content, no full-file content, no unredacted preview, no
raw absolute path, no context proposal, no context injection, no memory write,
no export, no approval execution, no tool execution, and no execution.

Explicitly: no raw file access, no mobile sensor access, and no background collection are added by M49.

Mobile approval records are safe-ref-only persistence. The default store is
local in-memory. Tests may pass an explicit local JSONL path to verify that
only safe refs are written. No repository data store, backend route, native
mobile storage, background collection, credential handling, cookie handling,
mobile sensor access, production persistence, or production authority is added.

The evaluator revalidates current object fields before capture so constructor
validation alone is not trusted. model_copy-mutated raw access, raw content,
full-file content, unredacted preview, context proposal, context injection,
memory write, export, execution, approval execution, mobile sensor access, and
background collection flags are denied.

`approval_test_` refs are test fixtures only and are never runtime authority.
Approval refs are identifiers, not authority.

M50 remains future. M50 is Mobile Approval Audit Hardening and must perform its
own implementation, validation, and strict pushed-release review before mobile
approval audit hardening is described as implemented.
