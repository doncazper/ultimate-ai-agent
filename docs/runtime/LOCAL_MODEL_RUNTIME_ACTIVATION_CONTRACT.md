# Local Model Runtime Activation Contract

Status: Active M22 contract documentation for v0.26.0. Contract-only.

M22 defines how future local model runtimes are represented before any runtime is activated. The contract covers Ollama, llama.cpp, MLX, vLLM, LM Studio, OpenAI-compatible local endpoints, and generic loopback HTTP runtime profiles as metadata-only planned profiles.

This patch adds a Local Model Runtime Activation Contract only. No model was called. No runtime was activated. No endpoint was contacted.

M22 adds:

- provider profile contracts.
- endpoint descriptor policy.
- activation policy, request, and decision contracts.
- health probe plan contracts.
- validation helpers, tests, verifiers, docs, and Foundation Gate criteria.

M22 does not add:

- real local model calls.
- no runtime execution.
- runtime activation.
- endpoint probes.
- no endpoint probe.
- provider SDK imports.
- runtime package imports.
- user prompt processing.
- tool execution.
- memory writes.
- backend API routes.
- OpenAPI path count changes.
- dependencies.

All M22 decisions are metadata-only and non-authoritative. Approval refs are identifiers only and cannot authorize activation. M23 remains future for any first bounded local model call.
