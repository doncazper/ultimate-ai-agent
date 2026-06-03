# Ultimate AI Agent Version

Current active baseline: **v0.30.1**

v0.30.1 hardens M26 Grounded Recall Router + Evidence-Linked Context Pack
Builder safety. It enforces consistency between source_ref prefixes and declared
source_kind, denies mismatched memory/model/runtime/OpenWebUI refs, prevents
caller-declared source_kind from upgrading source priority, adds regression
tests and Foundation Gate coverage for mismatch bypasses, and preserves safe
canonical/evidence/receipt/event source selection.

It adds no vector search, embeddings, RAG, external retrieval, model/provider
calls, memory writes, backend recall/search/injection routes, dependencies,
context injection runtime, or M27 work. OpenAPI path count remains `74`. M27
remains planned/provisional.
