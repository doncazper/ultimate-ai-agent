# Truth Source Priority

Status: Active for v0.29.0 / M25.

M25 source priority is deterministic:

- canonical docs.
- evidence manifests.
- receipts.
- Event Ledger records.
- user-reviewed sources.
- source-linked memory.
- reviewed memory.
- unreviewed memory.
- model output blocked.
- runtime output blocked.
- OpenWebUI output blocked.

Canonical files, evidence manifests, receipts, Event Ledger records, and
user-reviewed sources outrank memory. Memory is recall, not authority. Source
linked memory may support recall and context, but memory-only evidence cannot
verify truth. Model output is not evidence and cannot verify truth.
