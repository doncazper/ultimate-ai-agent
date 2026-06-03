# M23 To M24 Boundary

Status: Active M23-to-M24 boundary documentation for v0.27.1.

M23 is implemented/released as a manual fixed-prompt local call only. M24
remains future and is the Memory Provider Abstraction milestone.

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
Gate use fake transport. M24 remains future until a dedicated reviewed
milestone implements and gates it.
