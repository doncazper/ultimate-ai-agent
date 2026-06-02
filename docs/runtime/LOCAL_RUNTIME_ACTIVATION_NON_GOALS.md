# Local Runtime Activation Non-Goals

Status: Active M22 contract documentation for v0.27.0. Contract-only.

M22 explicitly does not implement:

- local model runtime activation.
- real local model calls.
- endpoint probes.
- provider SDK imports.
- runtime package imports.
- model loading.
- local service discovery.
- user prompt execution.
- raw prompt display.
- tool execution.
- memory writes.
- file writes.
- OpenWebUI runtime behavior.
- backend API routes.
- dependencies.
- production readiness claims.

No model was called. No runtime was activated. No endpoint was contacted.

M23 is implemented/released by v0.27.0 as a separate manual/CLI-only,
fixed-prompt-only local model call path. M23 does not authorize runtime
activation, endpoint probes, arbitrary prompts, user-content model calls, tool
execution, memory writes, file writes, dependencies, or production authority.
