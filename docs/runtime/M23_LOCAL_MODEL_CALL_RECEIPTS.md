# M23 Local Model Call Receipts

Status: Active M23 receipt documentation for v0.27.1.

M23 receipts are safe summary metadata only. They must record the fixed prompt
id, call-performed flag, redaction status, safe response summary if available,
and the non-authoritative model output flag.

Receipts must record:

- no tool execution.
- no memory write.
- no file write.
- no provider call.
- no remote call.
- raw responses are not stored.

Receipts must not expose raw prompts, raw responses, raw files, raw memory,
credentials, provider payloads, or secrets. A receipt is audit evidence, not
execution authority. Tests and Foundation Gate use fake transport. M24 remains
future.
