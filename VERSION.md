# Ultimate AI Agent Version

Current active baseline: **v0.30.0**

v0.30.0 implements M26: Grounded Recall Router + Evidence-Linked Context Pack
Builder. It adds deterministic local recall/context-pack contracts over
provided safe candidates, source priority that keeps source-backed refs above
memory, exclusion of unknown/arbitrary/stale/conflicted/revoked/deleted/model/
runtime/OpenWebUI/raw/secret candidates, safe summary-only context packs, tests,
docs, static verifier coverage, and Foundation Gate criteria.

It adds no backend routes, frontend features, vector search, embeddings,
semantic search, RAG ingestion, web search, external retrieval, source crawling,
arbitrary file reads, model/provider calls, local LLM calls, memory writes,
evidence mutation, Event Ledger mutation, context injection runtime, OpenWebUI
runtime bridge, dependencies, tool execution, or production authority. OpenAPI
path count remains `74`. M27 remains planned/provisional.
