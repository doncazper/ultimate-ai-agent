# Context Pack Safety

Status: active
Current through: v0.32.1
Purpose: Define M26 context-pack safety boundaries.

M26 context packs are evidence-linked planning artifacts containing safe
summaries and refs only. They are not execution authority and do not approve,
run, dispatch, inject, or mutate anything.

Safety rules:

- source_ref/source_kind consistency is required for selected items.
- caller-declared source_kind cannot upgrade memory/model/runtime/OpenWebUI
  refs into context-pack authority.
- no raw prompt, file, memory, transcript, model-output, provider, or credential
  payloads.
- no model/provider calls.
- no local LLM calls.
- no web search or external retrieval.
- no vector database, semantic search, or embedding runtime.
- no context injection into prompts, OpenWebUI, local runtimes, tools, or memory.
- no backend API route additions.
- no frontend controls.
- no memory writes.

Context packs may be used for review and planning only until a later reviewed
milestone explicitly authorizes runtime integration.
