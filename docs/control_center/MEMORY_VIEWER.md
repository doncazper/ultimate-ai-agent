# Memory Viewer

Status: Current for v0.21.0 / M17.

The Memory Viewer is a Web Control Center read-only and summary-only surface for memory record refs. It shows safe refs, memory type, source refs, confidence status, review status, staleness, conflict indicators, data classification, redaction status, and related evidence/event/receipt refs.

No backend route is added for M17. The current Web Control Center memory view uses frontend mock summaries only and cannot write, learn, forget, edit, or delete memory.

memory is recall, not authority. canonical files and governed source systems outrank memory.

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
