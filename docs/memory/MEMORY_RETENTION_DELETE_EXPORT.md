# Memory Retention Delete Export

M24 defines retention, delete, and export contracts for reviewed local memory records. Retention states include active, expired, deletion requested, deleted, export only, archived, and blocked.

Delete marks records as deleted/revoked style governance state for auditability. Export is redacted-summary-only. Raw export is blocked. Secrets, credentials, raw prompts, raw model outputs, raw files, raw transcripts, raw memory contents, and raw session history must not be exported.

Memory is recall, not authority. Memory is not ground truth. Canonical files, evidence manifests, receipts, Event Ledger records, and user-reviewed sources outrank memory.

M24 adds no backend memory mutation API and no production persistence claim.
