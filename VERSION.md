# Ultimate AI Agent Version

Current active baseline: **v0.27.1**

v0.27.1 hardens M23 First Real Local LLM Call safety. It strengthens
fixed-prompt enforcement, loopback endpoint policy, approval gating, CLI dry-run
defaults, fake/manual transport separation, response size caps, response
redaction, non-authoritative output guarantees, documentation, static safety
verification, Foundation Gate coverage, and Foundation Gate report atomic
write/replace safety.

It adds no arbitrary user prompts, cloud provider calls, provider SDKs,
tokenizer or billing APIs, backend execute routes, Control Center execute
controls, OpenWebUI runtime bridge, tool execution, memory writes, file writes,
remote execution, dependencies, runtime behavior expansion, or production
authority. OpenAPI path count remains `74`. M24 remains the future Memory
Provider Abstraction milestone.
