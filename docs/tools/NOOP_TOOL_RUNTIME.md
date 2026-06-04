# No-Op Tool Runtime

Status: active M31 documentation.
Current active baseline: **v0.35.1**

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

v0.35.1 ensures the no-op result cannot be obtained by mutating a pre-built
request with hidden dynamic dispatch fields or hidden side-effect fields.
Metadata is revalidated as part of the evaluator boundary, so caller-declared
module paths, callable names, alternate tool refs, side-effect lists, file-write
requests, environment reads, or secret lookups are denied before the no-op
adapter can complete.

`execution_performed=True` may appear only to indicate that this deterministic
no-op invocation completed. `side_effects_performed=[]` is required.

M32-M40 remain planned/provisional.
