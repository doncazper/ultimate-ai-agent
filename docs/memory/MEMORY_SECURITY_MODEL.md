# Memory Security Model

Primary risks:

- secret storage.
- unreviewed profiling.
- stale false beliefs.
- hallucination writes.
- model-output writes.
- local LLM output writes.
- OpenWebUI transcript writes.
- mobile capture writes.
- tool output writes.
- file-content leaks.
- authoritative-memory misuse.

Controls:

- user review required.
- redacted summary-only records.
- provenance and source refs required.
- delete and redacted export contracts.
- no automatic writes.
- no model-output writes.
- no local LLM output writes.
- no OpenWebUI chat memory writes.
- no mobile capture writes.
- no tool output writes.
- no vector DB or embeddings.
- no cloud memory.
- no raw session history.
- no context injection.

Memory is recall, not authority. Memory is not ground truth. Canonical files, evidence manifests, receipts, Event Ledger records, and user-reviewed sources outrank memory.
