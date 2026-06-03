# Ultimate AI Agent Version

Current active baseline: **v0.29.2**

v0.29.2 hardens local-dev API authority and raw preview safety before M26. It
removes test-prefixed approval-ref fallback authority from Tool Broker/kernel
mutation paths, keeps public `/kernel/tasks/run` local-dev mutation requests
dry-run-only, returns metadata-only file read previews by default, prevents
raw exception-message echo from API handlers, and makes truth memory/model
authority helpers fail closed when unsafe refs are passed directly.

It adds no web search, external verification, model/provider calls,
retrieval/RAG/vector/embedding functionality, memory writes, backend truth
verification routes, dependencies, M26 context-pack builder, backend route
expansion, or production authority. OpenAPI path count remains `74`. M26
remains future.
