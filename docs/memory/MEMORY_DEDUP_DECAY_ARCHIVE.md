# Memory Dedup Decay Archive

M24 borrows dedup, decay, and archive planning vocabulary as metadata only. Fields such as `dedup_key`, `last_referenced_at`, `importance_score`, `decay_state`, and `archive_candidate` help future review without adding runtime automation.

There is no decay scanner in M24. There is no semantic dedup, vector DB, embeddings, cron job, background worker, Redis, Qdrant, ARQ, Docker service, automatic extraction, session-end learning, or auto-curated wiki.

Memory is recall, not authority. Memory is not ground truth. Canonical files, evidence manifests, receipts, Event Ledger records, and user-reviewed sources outrank memory.
