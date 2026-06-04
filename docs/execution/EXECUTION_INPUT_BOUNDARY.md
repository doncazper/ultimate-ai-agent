# Execution Input Boundary

Status: active M30 source-of-truth documentation.

M30 accepts safe refs and safe summaries only. Raw prompt, raw model output,
raw file content, raw transcripts, raw runtime output, and secret-like content
are denied at constructor and evaluator boundaries.

Refs that cannot authorize execution:

- model output refs.
- runtime output refs.
- OpenWebUI refs.
- memory refs.
- context-pack refs.
- tool-intent refs.
- approval refs.
- approval decision refs.
- Control Center preview refs.
- unknown refs.

Canonical, evidence, receipt, event, and user-reviewed refs may explain why a
state transition is reviewable, but they do not authorize real execution.

M30 input boundaries add no context injection, no RAG, no embeddings, no vector
search, no external retrieval, and no model/provider calls.

M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool. M32-M40 remain planned/provisional.
