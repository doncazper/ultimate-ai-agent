# Tool Runtime Receipt Plan

Status: active M31 documentation.
Current active baseline: **v0.35.0**

M31 receipt plans are non-authoritative summaries for the no-op runtime
invocation. They record the invocation ref, the no-op tool ref, and safe status
metadata only.

Receipt plans must not store raw input or raw output. They must not write
memory, mutate the Event Ledger, perform network/model/provider calls, execute
shell commands, mutate files, enable plugins, or authorize future execution.

For the no-op invocation, `execution_performed=True` means only that the
deterministic no-op adapter path completed. `side_effects_performed=[]` is
required.

M32-M40 remain planned/provisional.
