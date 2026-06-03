# Memory Provider Abstraction

M24 defines the `MemoryProvider` abstraction for reviewed, source-linked recall records. Memory is recall, not authority. Memory is not ground truth. Canonical files, evidence manifests, receipts, Event Ledger records, and user-reviewed sources outrank memory.

Allowed in M24:

- local in-memory provider for tests and dev review.
- optional explicit-path stdlib SQLite local store.
- redacted summary-only memory records.
- required `source_refs`, plus supplemental evidence, event, receipt, and file refs.
- trust and confidence metadata as advisory metadata only.

Blocked in M24:

- no automatic writes.
- no model-output writes.
- no local LLM output writes.
- no OpenWebUI chat memory writes.
- no Control Center memory mutation.
- no mobile capture writes.
- no tool output writes.
- no cloud memory provider.
- no vector DB or embeddings.
- no raw session history.
- no context injection.
- no production persistence claim.

M25 is now implemented/released separately as the Truth Source Router + Evidence
Claim Checker milestone. It keeps memory below governed truth sources and adds
no memory authority, automatic memory write, context injection, vector DB,
embedding, web search, model/provider call, backend mutation route, or
production authority.
