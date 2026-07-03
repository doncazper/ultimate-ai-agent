# Memory Write Policy

M24 allows only explicit reviewed memory record contracts. A write must be user-reviewed, source-linked, redacted summary-only, local-only, and non-authoritative. `source_refs` are required for M24 local-store writes; evidence, event, and receipt refs are supplemental provenance and do not replace `source_refs`.

FCC-V1-005 implements one narrow reviewed recall-write lane: backend-owned
Memory Review accept/correct decisions may create reviewed recall-only
`LocalMemoryStore` records from safe summaries and safe refs after user review,
exact `LocalApprovalAuthority` validation, idempotency, receipt creation,
safe-disable posture, and Evidence Timeline recording. The exact scope is
`exact-scope-ref:memory-review:accept-correct-reviewed-recall-write`; safe
disable is `safe-disable-ref:memory-review:accept-correct-reviewed-recall-write`;
rollback posture is `rollback-ref:memory-review:suppress-reviewed-recall-record`
with rollback execution blocked. This is not Control Center-owned mutation,
automatic memory writing, source-truth authority, reusable approval authority,
context injection, connector/CRM/account sync, action execution, delete/export
execution, public beta, or production authority. Reject decisions preserve
review state and create no recall record.

Denied in M24:

- no automatic writes.
- no model-output writes.
- no local LLM output writes.
- no OpenWebUI chat memory writes.
- no Control Center memory mutation.
- no mobile capture writes.
- no tool output writes.
- no raw prompt, raw model output, raw file content, raw transcript, secret, or credential storage.
- no forbidden data classification.
- no raw export.

Memory is recall, not authority. Memory is not ground truth. Canonical files, evidence manifests, receipts, Event Ledger records, and user-reviewed sources outrank memory.

Future writes from model, chat, mobile, or tool outputs require later reviewed
milestones. M25 implements truth/evidence checking only and adds no memory
write path.
