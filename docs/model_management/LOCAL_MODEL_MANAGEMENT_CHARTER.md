# M152 Local Model Management Charter

M152 local model management is a post-M151, contract-only, review-only,
metadata-only, local-only, safe-ref-only charter for the future self-managed
model layer.

The charter records model refs, model profile refs, model artifact refs, injected
hardware summary refs, inert search terms, candidate summary refs, llama.cpp
settings-plan refs, redacted observability refs, audit refs, replay refs, and
no-effect receipt-plan refs.

The default state is disabled by default and route-free. A `qwopus` search term
is only inert review metadata in M152. It is not a live Hugging Face query, a
download request, a model load request, a provider call, or a prompt.

UAA remains the authority boundary. `core/model_router` owns model selection
metadata, while `core/model_runtime` owns planned runtime contract refs such as
the llama.cpp settings plan. OpenWebUI remains a shell, not the agent brain.

M152 has no network access, no subprocess, no llama.cpp import, no llama.cpp
server, no Hugging Face hub import, no Hugging Face hub download, no downloads,
no model load, no model unload, no model delete, no model/provider call, no
backend route, no Control Center execute control, no dependency, no memory
write, no context injection, no tool execution, and no production authority.
