# Evidence, File, And Memory Viewer Safety

Status: Current for v0.21.0 / M17.

M17 adds governed Web Control Center read-only and summary-only viewers for evidence refs, file refs, and memory refs. The patch is frontend-only and uses visibly mock, non-authoritative data.

No backend route is added for M17. OpenAPI path count remains unchanged at 74.

Allowed display:
- safe refs
- redacted summaries
- data classification labels
- timestamp and status metadata
- provenance and relation summaries
- staleness and conflict indicators

Forbidden display and capability:
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
- no runtime/model/provider calls
- no remote dispatch
- no mobile sensor access
- no plugin enablement

Memory is recall, not authority. Canonical files and governed source systems outrank memory. Evidence and file refs are safe inspection metadata only, not authority to bypass approvals or execute actions locally.
