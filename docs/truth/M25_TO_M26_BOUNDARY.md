# M25 To M26 Boundary

Status: Active for v0.29.2 / M25.

M25 validates claim and evidence refs. M25 does not build context packs. M25
does not add recall routing. M25 does not add context injection. M25 does not
inject content into OpenWebUI, a model prompt, or a runtime.

M25 validation denies arbitrary refs, inferred unknown source kinds, explicit
`TruthSourceKind.unknown` evidence, and self-verifying refs. Recognized
structured refs are required before a claim can become `source_linked`,
`evidence_supported`, or `verified_by_primary_source`.

M26 remains future as Grounded Recall Router + Evidence-Linked Context Pack
Builder. Future M26 work may plan safe recall/context-pack candidates, but it
must still avoid vector search, embeddings, RAG ingestion, external retrieval,
model calls, provider calls, memory writes, and context injection runtime unless
a later reviewed milestone explicitly changes those boundaries.
