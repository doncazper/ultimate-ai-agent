# Local Memory Store

M24 adds a local-only memory store foundation. It supports in-memory storage for tests/dev and explicit-path SQLite using Python stdlib `sqlite3`. There is no default repo data file, no home-directory database, no daemon, no background worker, and no production persistence claim.

The local store accepts only reviewed, source-linked, redacted summary records. Memory is recall, not authority, and memory is not ground truth. Canonical files, evidence manifests, receipts, Event Ledger records, and user-reviewed sources outrank memory.

The local store does not add backend memory mutation routes. OpenAPI path count remains unchanged at `74`.

M24 adds no automatic writes, model-output writes, local LLM output writes, OpenWebUI chat memory writes, mobile capture writes, tool output writes, vector DB, embeddings, cloud provider, raw session history, context injection, or production runtime.
