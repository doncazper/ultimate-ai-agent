# Ultimate AI Agent Version

Current active baseline: **v0.28.1**

v0.28.1 repairs the M24 public memory request contract by making package-root
MemoryWriteRequest exports align with the provider/store write path, updates
route inventory docs through v0.28.1, hardens M24 Foundation Gate guard-field
tests, clarifies M24 source_refs write-validation messaging, returns defensive
copies from the in-memory local store, and applies minor memory docs/code
polish.

It adds no automatic memory writes, model/local-LLM/OpenWebUI/mobile/tool memory
writes, backend mutation routes, vector DB, embeddings, cloud memory, context
injection, dependencies, or M25 work. OpenAPI path count remains `74`.
