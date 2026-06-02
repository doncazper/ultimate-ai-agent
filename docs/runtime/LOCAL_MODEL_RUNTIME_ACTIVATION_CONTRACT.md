# Local Model Runtime Activation Contract

Status: Active M22 contract documentation for v0.26.1. Contract-only.

M22 defines how future local model runtimes are represented before any runtime is activated. The contract covers Ollama, llama.cpp, MLX, vLLM, LM Studio, OpenAI-compatible local endpoints, and generic loopback HTTP runtime profiles as metadata-only planned profiles.

This patch adds a Local Model Runtime Activation Contract only. No model was called. No runtime was activated. No endpoint was contacted.

M22 adds:

- provider profile contracts.
- endpoint descriptor policy.
- activation policy, request, and decision contracts.
- health probe plan contracts.
- validation helpers, tests, verifiers, docs, and Foundation Gate criteria.

M22 does not add:

- no real local model calls.
- no runtime activation.
- no runtime execution.
- no endpoint probe.
- no health probe.
- no provider SDK imports.
- no runtime package imports.
- no tokenizer packages.
- no billing APIs.
- no user prompt processing.
- no tool execution.
- no memory writes.
- no OpenWebUI runtime bridge behavior.
- no backend API routes.
- no OpenAPI path count changes.
- no dependencies.

All M22 decisions are metadata-only and non-authoritative. Approval refs are identifiers only and cannot authorize activation. M23 remains future for any first bounded local model call.
