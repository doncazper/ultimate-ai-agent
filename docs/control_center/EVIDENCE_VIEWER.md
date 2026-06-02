# Evidence Viewer

Status: Current for v0.21.0 / M17.

The Evidence Viewer is a Web Control Center read-only and summary-only surface for governed evidence refs. It shows safe refs, redacted metadata, source type summaries, claim refs, event refs, receipt refs, file refs, memory refs, confidence status, provenance summary, and redaction status.

No backend route is added for M17. The current Web Control Center evidence view uses frontend mock summaries only and is visibly non-authoritative.

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

Evidence summaries are not authority to execute or approve anything. Python Agent Core, Approval Authority, Event Ledger, Consent Ledger, Tool Broker, Secret Broker, Redaction, and Foundation Gate remain the governing boundary.
