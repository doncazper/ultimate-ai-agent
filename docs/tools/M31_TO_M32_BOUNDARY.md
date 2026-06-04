# M31 to M32 Boundary

Status: active M31 documentation.
Current active baseline: **v0.35.0**

M31 is implemented/released as Real Tool Runtime Adapter, Single Safe No-Op
Tool.

M31 allows only the deterministic no-op tool:

```text
tool:no_op.v1
```

M31 does not add arbitrary tool execution, dynamic dispatch, side-effecting
tools, shell/subprocess execution, file mutation, memory writes, network calls,
model/provider calls, browser/mobile/remote/plugin tools, backend execute
routes, Control Center execute controls, dependencies, context injection, or
production authority.

M32-M40 remain planned/provisional. Broader real safe tool runtime expansion
requires a separate reviewed milestone and cannot inherit authority from M31.
