# File Reference Viewer

Status: Current for v0.21.1 / M17.

The File Reference Viewer is a Web Control Center read-only and summary-only surface for file refs. It shows safe filename labels, file kind, size summary, data classification, source surface, event refs, receipt refs, evidence refs, redaction status, and safe refs.

No backend route is added for M17. The current Web Control Center file ref view uses frontend mock summaries only and does not browse or open local paths.

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

File refs are identifiers and safe metadata only. The UI does not expose raw path disclosure, file body text, write controls, delete controls, import controls, or broad filesystem scanning.
