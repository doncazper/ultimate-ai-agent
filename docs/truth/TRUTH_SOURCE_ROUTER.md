# Truth Source Router

Status: Active for v0.29.1 / M25.

M25 adds a deterministic local Truth Source Router over explicitly provided
source refs and evidence refs. It answers why a claim may be believed by ranking
provided refs, not by discovering new facts.

The router performs no external verification. It performs no web search. It
performs no source fetching. It performs no model calls, no provider calls,
local LLM calls, tool execution, no memory writes, no evidence mutation, Event Ledger
mutation, retrieval/RAG, vector DB lookup, or embeddings.

Memory is recall, not authority. Memory is not ground truth. Model output,
runtime output, OpenWebUI output, and Control Center output cannot verify
truth. Arbitrary refs are not authority.

Unknown or unrecognized source refs are denied. Explicit
`TruthSourceKind.unknown` evidence cannot support truth verification.

M25 adds no backend route and keeps OpenAPI path count at `74`.
