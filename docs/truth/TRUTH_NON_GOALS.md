# Truth Non Goals

Status: Active for v0.29.2 / M25.

M25 does not add:

- autonomous fact checking.
- web search.
- external verification.
- external retrieval.
- source crawling.
- arbitrary file reads.
- model verification.
- model calls.
- no provider calls.
- local LLM calls.
- retrieval/RAG.
- vector DB.
- embeddings.
- no memory writes.
- no evidence mutation.
- Event Ledger mutation.
- Control Center mutation controls.
- backend mutation routes.
- production truth service.

M25 also does not treat arbitrary refs, inferred unknown source kinds, or
explicit `TruthSourceKind.unknown` evidence as verification authority.
