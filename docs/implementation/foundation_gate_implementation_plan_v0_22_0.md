# Foundation Gate Implementation Plan v0.22.0

Status: Current Foundation Gate implementation plan for v0.22.0.

v0.22.0 adds M18 Local Runtime Status + Manual Smoke Control Surface safety coverage.

New criterion:

- `m18_local_runtime_manual_smoke_surface_safe`

The criterion verifies:

- `/runtime/local` exists as a read-only local runtime status surface.
- `/runtime/manual-smoke` exists as a manual smoke report validation-only surface.
- M18 mock data is visibly mock, non-authoritative, redacted summary-only, and free of raw report content.
- static frontend verifier coverage rejects runtime/smoke execution endpoints, dangerous runtime controls, raw smoke fields, and credential-like fields.
- OpenAPI path count remains `74`.
- no backend route is added.

Safety boundary:

- no runtime execution.
- no manual smoke execution.
- no model/provider calls.
- no remote execution.
- no mobile sensor access.
- no plugin enablement.
- no native build workflow.
- no OpenWebUI integration.
- no raw smoke report, no raw prompts, no raw response bodies, no credentials, and no provider payloads.

## Skill Package Security Rule

v0.22.0 does not change the Skill Package Security Rule. It adds no plugin enablement, tool installation, native build workflow, Computer Use automation, Chrome authenticated profile control, or external action.

All skills are untrusted packages by default until a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities exist.
