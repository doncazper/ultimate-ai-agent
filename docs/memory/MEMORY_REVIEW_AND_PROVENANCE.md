# Memory Review And Provenance

M24 memory records carry provenance metadata: required source refs, supplemental evidence refs, event refs, receipt refs, file refs, user review refs, review state, source priority, and metadata refs. Evidence, event, and receipt refs add audit context, but they do not replace required `source_refs` for local-store writes. These references make memory auditable without making memory authoritative.

FCC-V1-005 Memory Review decisions preserve this boundary. Accept/correct
decisions are backend-owned, idempotent, receipt-backed, and evidence-visible;
they may create reviewed recall-only records from safe summaries and refs.
Reject decisions preserve rejected state and create no recall record. No
decision stores raw corrected/source content or grants context injection, truth
authority, connector/CRM/account sync, provider/model authority, action
execution, public beta, or production authority.

Review states include draft, user review required, user reviewed, stale, conflicted, superseded, revoked, deleted, and blocked. Memory can be wrong, stale, conflicting, superseded, revoked, or deleted.

Memory is recall, not authority. Memory is not ground truth. Canonical files, evidence manifests, receipts, Event Ledger records, and user-reviewed sources outrank memory.

M24 has no automatic extraction, no raw session history, no OpenWebUI chat memory writes, no mobile capture writes, no tool output writes, and no context injection.
