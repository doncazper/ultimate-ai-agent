# Local Model Management Non-Goals

M152 local model management does not implement runtime model management. It is a
post-M151 planning and validation boundary.

M152 does not:

- Search Hugging Face.
- Import a Hugging Face hub client.
- Download GGUF artifacts.
- Read raw model files or raw model cards.
- Inspect the real system hardware.
- Spawn a process.
- Start a llama.cpp server.
- Build shell strings or execute argv.
- Apply llama.cpp settings.
- Edit OpenWebUI settings.
- Add Control Center controls.
- Add API routes.
- Add dependencies.
- Load, unload, delete, or call a model.
- Log raw prompts, completions, provider payloads, stack traces, raw paths, or
  environment variables.

The only expected output is no-effect, safe-ref-only review metadata that can be
audited before later milestones add live authority.
