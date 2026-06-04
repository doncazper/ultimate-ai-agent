# Tool Runtime Receipt Plan

Status: active M32 documentation.
Current active baseline: **v0.36.1**

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

M33-M40 remain planned/provisional.
