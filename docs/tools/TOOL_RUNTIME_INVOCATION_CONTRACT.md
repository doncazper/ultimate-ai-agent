# Tool Runtime Invocation Contract

Status: active M31 documentation.
Current active baseline: **v0.35.0**

M31 defines typed invocation contracts for a single safe no-op runtime path:

- `ToolRuntimeManifest`
- `ToolRuntimeAdapterDescriptor`
- `ToolRuntimePolicy`
- `ToolInvocationRequest`
- `ToolInvocationDecision`
- `ToolInvocationResult`
- `ToolInvocationReceiptPlan`
- `NoOpToolInput`
- `NoOpToolOutput`

Invocation requests must provide structured refs, a replay key, a safe summary,
and the exact no-op tool identity. Unknown tools, mismatched tool names,
effectful refs, raw prompt/model/file/transcript flags, secret-like metadata,
and model_copy-mutated unsafe fields are denied at the evaluator boundary.

The no-op result envelope is deterministic and redacted. It does not echo raw
input, does not store raw content, and reports `side_effects_performed=[]`.

No backend execute route is added in M31.

M32-M40 remain planned/provisional.
