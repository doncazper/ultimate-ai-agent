# M167 Live Model Production Hardening Boundary

M167 is a live production hardening evidence boundary for the local llama.cpp
and OpenWebUI layer. It is not a new runtime authority switch.

The accepted boundary is:

- M166 remains the production authority gate.
- M167 requires actual live evidence and reviewed live evidence before a report
  can pass.
- Evidence is redacted summary only, safe-ref-only, localhost-only,
  audit-bound, replay-safe, rollback-bound, and exact-scope-bound.
- OpenWebUI remains a shell pointed at UAA's local `/v1` gateway.
- Control Center may show reviewed status in a later UI milestone, but M167
  adds no Control Center control.

The denied boundary is:

- no raw prompt
- no raw response
- no raw provider payload
- no credential
- no raw local path
- no raw log
- no username
- no env dump
- no backend route
- no Control Center control
- no OpenWebUI admin
- no OpenWebUI plugin
- no dependency
- no unreviewed side effects

The M167 hardening report does not add web fetching, model downloads, process
starts, llama.cpp launches, OpenWebUI calls, or load-test execution by itself.
The separate `docs/production/M167_OPENWEBUI_LOCAL_INSTALLER.md` slice permits
only the explicit, operator-approved OpenWebUI Docker image pull through
`uaa setup install --target openwebui`. Other actions may be performed only by
already approved live lanes, and M167 records the reviewed evidence refs that
prove they happened safely.
