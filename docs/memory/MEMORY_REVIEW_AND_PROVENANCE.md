# Memory Review And Provenance

M24 memory records carry provenance metadata: source refs, evidence refs, event refs, receipt refs, file refs, user review refs, review state, source priority, and metadata refs. These references make memory auditable without making memory authoritative.

Review states include draft, user review required, user reviewed, stale, conflicted, superseded, revoked, deleted, and blocked. Memory can be wrong, stale, conflicting, superseded, revoked, or deleted.

Memory is recall, not authority. Memory is not ground truth. Canonical files, evidence manifests, receipts, Event Ledger records, and user-reviewed sources outrank memory.

M24 has no automatic extraction, no raw session history, no OpenWebUI chat memory writes, no mobile capture writes, no tool output writes, and no context injection.
