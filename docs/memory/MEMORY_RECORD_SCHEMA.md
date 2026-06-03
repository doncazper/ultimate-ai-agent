# Memory Record Schema

M24 memory records are structured, reviewed recall records. Required safety concepts include `memory_id`, `memory_kind`, `memory_layer`, `provider_kind`, `review_state`, `authority_level`, `source_priority`, `data_classification`, `safe_summary`, source refs, evidence refs, event refs, receipt refs, file refs, confidence metadata, trust metadata, retention state, redaction status, and lifecycle metadata.

Planning metadata includes `dedup_key`, `last_referenced_at`, `importance_score`, `decay_state`, `archive_candidate`, `context_pack_eligible`, `injection_priority`, and recall budget hints. These fields are metadata only. M24 has no context injection.

Records must not contain raw prompts, raw model outputs, raw files, raw transcripts, secrets, credentials, private keys, unredacted sensitive content, raw provider payloads, raw memory contents, or raw session history.

Memory is recall, not authority. Memory is not ground truth. Canonical files, evidence manifests, receipts, Event Ledger records, and user-reviewed sources outrank memory.
