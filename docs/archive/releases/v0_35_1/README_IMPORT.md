# README Import v0.35.1

Status: historical release packet for the current active baseline.

Current active baseline: **v0.35.1**

v0.35.1 hardens M31 Real Tool Runtime Adapter, Single Safe No-Op Tool. It
preserves the no-op-only runtime adapter from v0.35.0 while strengthening
allowlist validation, tool_ref/tool_name consistency, dynamic dispatch denial,
hidden side-effect denial, authority-boundary checks, evaluator revalidation,
replay protection, static verification, documentation, and Foundation Gate
coverage.

The only allowed runtime invocation remains `tool:no_op.v1`. Hidden
model_copy-mutated fields and metadata cannot introduce module loading,
callable/function dispatch, alternate tool refs, file/memory/network/model/
shell/browser/mobile/remote/plugin actions, environment reads, or secret
lookups.

OpenAPI path count remains `74`. M32-M40 remain planned/provisional.
