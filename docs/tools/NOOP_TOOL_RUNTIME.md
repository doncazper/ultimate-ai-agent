# No-Op Tool Runtime

Status: active M31 documentation.
Current active baseline: **v0.35.0**

The only runtime tool enabled in M31 is the deterministic no-op tool:

```text
tool_ref: tool:no_op.v1
tool_name: noop
```

The no-op tool returns a fixed safe status:

```text
NOOP_TOOL_COMPLETED
```

The no-op tool does not echo raw input, read files, write files, write memory,
call network endpoints, call models/providers, run shell commands, automate a
browser, access mobile/device APIs, execute remotely, enable plugins, or inject
context.

`execution_performed=True` may appear only to indicate that this deterministic
no-op invocation completed. `side_effects_performed=[]` is required.

M32-M40 remain planned/provisional.
