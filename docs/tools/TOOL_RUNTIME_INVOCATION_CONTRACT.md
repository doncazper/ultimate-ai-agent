# Tool Runtime Invocation Contract

Status: active M31 documentation.
Current active baseline: **v0.35.1**

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

v0.35.1 hardens this boundary by revalidating hidden model_copy-mutated fields
and metadata before any no-op result can be returned. Caller-provided
`module_path`, `callable_name`, `function_name`, registry/handler fields,
alternate `tool_ref` or `tool_name` fragments, and metadata-backed dynamic
dispatch hints are denied with `DYNAMIC_DISPATCH_DENIED`. Hidden or
metadata-backed side-effect requests such as file writes, memory writes,
network calls, model calls, shell commands, environment reads, browser/mobile/
remote/plugin actions, and secret lookups are denied with
`SIDE_EFFECT_ATTEMPT_DENIED`.

The no-op result envelope is deterministic and redacted. It does not echo raw
input, does not store raw content, and reports `side_effects_performed=[]`.

No backend execute route is added in M31.

M32-M40 remain planned/provisional.
