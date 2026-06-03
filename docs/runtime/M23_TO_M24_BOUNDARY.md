# M23 To M24 Boundary

Status: Historical M23-to-M24 boundary documentation; M24 is implemented by v0.28.0.

M23 is implemented/released as a manual fixed-prompt local call only. M24 is implemented/released by v0.28.0 as Memory Provider Abstraction + Local Memory Store.

M23 does not implement:

- memory provider abstraction.
- local memory store.
- memory ingestion.
- memory write from model output.
- arbitrary prompt input.
- user-content model calls.
- runtime activation.
- endpoint probes.
- backend model execution routes.
- OpenWebUI runtime bridge.
- Control Center execution.

M23 output is non-authoritative and cannot become memory authority. Responses
are capped and redacted, raw responses are not stored, and tests and Foundation
Gate use fake transport.

M24 memory is recall, not authority. M24 adds no model-output writes, local LLM output writes, automatic writes, context injection, vector DB, embeddings, cloud memory provider, backend mutation route, or production persistence. M25 is now implemented separately as deterministic local truth/evidence contracts and still does not make memory authority.
