# Master Plan v0.35.1

Status: historical release packet for the current active baseline.

Current active baseline: **v0.35.1**

v0.35.1 hardens M31 so the Python Agent Core can complete exactly one governed,
deterministic, redacted, side-effect-free no-op runtime adapter invocation
without allowing caller-mutated requests to smuggle dynamic dispatch or
side-effect requests past constructor validation.

Scope:

- tool allowlist and tool_ref/tool_name consistency hardening.
- dynamic dispatch denial for hidden and metadata-backed module/callable fields.
- side-effect denial for hidden and metadata-backed effect requests.
- authority-boundary denial for approval refs, plans, context packs, memory,
  tool-intent, model, runtime, OpenWebUI, and arbitrary refs.
- evaluator revalidation for model_copy-mutated invocation requests.
- replay protection and deterministic safe result handling.
- Foundation Gate, static verifier, tests, and docs.

Non-goals:

- arbitrary tool execution.
- side-effecting tools.
- shell/subprocess execution.
- file mutation.
- memory writes.
- network/model/provider calls.
- browser/mobile/remote/plugin tools.
- backend execute routes.
- Control Center execute controls.
- dependencies.
- M32 work.
- production authority.

M32-M40 remain planned/provisional.
