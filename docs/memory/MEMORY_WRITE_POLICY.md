# Memory Write Policy

M24 allows only explicit reviewed memory record contracts. A write must be user-reviewed, source-linked, redacted summary-only, local-only, and non-authoritative. `source_refs` are required for M24 local-store writes; evidence, event, and receipt refs are supplemental provenance and do not replace `source_refs`.

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

Future writes from model, chat, mobile, or tool outputs require later reviewed milestones. M25 remains future.
