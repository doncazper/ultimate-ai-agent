# Tool Runtime Receipt Plan

Status: active M32 documentation.
Current active baseline: **v0.37.1**

M32 receipt plans are non-authoritative summaries for allowlisted runtime
invocations.

Receipt plans may record:

- invocation ref.
- tool ref.
- safe status.
- `side_effects_performed=[]`.

Receipt plans must not store raw input, raw output, raw file content, text
previews, content hashes, directory listings, absolute local paths, symlink
targets, memory writes, Event Ledger mutations, shell output, network/model
payloads, or production authority.

For no-op and filesystem metadata invocations, `execution_performed=True` means
only that the deterministic governed adapter path completed. It does not mean
action execution or filesystem mutation happened.

M33 redacted preview receipt plans are non-authoritative and store no raw file
content, no raw prompt, no raw model output, no raw transcript, no secret-like
values, and no raw absolute paths. v0.37.4 supersedes the future roadmap and M34-M60 remain planned/provisional.
