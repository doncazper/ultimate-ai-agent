# Memory Viewer

Status: Active M17 viewer, still enforced under v0.28.2.

The Memory Viewer is a Web Control Center read-only and summary-only surface for memory record refs. It shows safe refs, memory type, source refs, confidence status, review status, staleness, conflict indicators, data classification, redaction status, and related evidence/event/receipt refs.

No backend route is added for M17. The current Web Control Center memory view uses frontend mock summaries only and cannot write, learn, forget, edit, or delete memory.

Memory is recall, not authority. Memory is not ground truth. Canonical files, evidence manifests, receipts, Event Ledger records, and user-reviewed sources outrank memory.
Canonical files and governed source systems outrank memory.

M24 adds governed local memory provider/store contracts, but the Control Center Memory Viewer remains read-only and summary-only. It cannot create, write, learn, forget, edit, delete, export raw content, or mutate memory.

Safety boundary:
- no raw prompts
- no raw secrets
- no raw file contents
- no raw memory contents
- no raw evidence payloads
- no raw credentials
- no raw provider payloads
- no file mutation
- no memory mutation
- no filesystem browsing
- no execution controls

Memory summaries must never be displayed as truth authority. Conflicts and stale memory are inspection signals only; governed source systems decide the safe next step.
