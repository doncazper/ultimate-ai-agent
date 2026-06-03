# Recall Non-Goals

Status: active
Current through: v0.31.0
Purpose: State what M26 does not implement.

M26 does not add:

- no vector search.
- no embeddings.
- semantic search.
- RAG ingestion.
- source crawling.
- arbitrary filesystem reads.
- web search.
- no external retrieval.
- autonomous fact checking.
- model/provider calls.
- local LLM calls.
- memory writes.
- evidence mutation.
- Event Ledger mutation.
- context injection runtime.
- OpenWebUI runtime bridge.
- backend recall/context-pack routes.
- Control Center context-inject controls.
- dependencies.
- production authority.

The Grounded Recall Router and Context Pack Builder are deterministic local
contract logic over provided refs only. They do not let caller-declared
source_kind upgrade memory/model/runtime/OpenWebUI refs or bypass source_ref
identity checks.
