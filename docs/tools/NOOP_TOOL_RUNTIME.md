# No-Op Tool Runtime

Status: active M32 documentation.
Current active baseline: **v0.36.0**

The deterministic no-op tool remains enabled in M32:

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

M32 also enables one safe local filesystem metadata tool. The no-op tool does
not authorize that tool, and the metadata tool does not authorize any broader
tool execution.

M33-M40 remain planned/provisional.
