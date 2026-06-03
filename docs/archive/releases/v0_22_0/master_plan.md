Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent Master Plan v0.22.0

Status: Historical master plan for v0.22.0.

v0.22.0 implements M18 Local Runtime Status + Manual Smoke Control Surface in CCC Web.

Implemented scope:

- `/runtime/local` shows read-only local runtime readiness and capability matrix summaries.
- `/runtime/manual-smoke` shows validation-only manual smoke report summaries.
- frontend mocks remain visibly mock, non-authoritative, and redacted summary-only.
- frontend tests cover M18 route headings, safety copy, and absent runtime/smoke execution controls.
- `scripts/verify_control_center_frontend.py` rejects M18 execution endpoints, dangerous runtime/smoke labels, raw report fields, and credential-like fields.
- Foundation Gate criterion `m18_local_runtime_manual_smoke_surface_safe` verifies the frontend surface, docs, static verifier, and OpenAPI route guard.

Architecture boundary:

- Python Agent Core remains the brain.
- Web Control Center is a governance/status/preview client only.
- OpenAPI path count remains unchanged at `74`.
- no backend route is added.
- manual smoke execution remains CLI-only, fixed-prompt-only, approval-gated, and non-authoritative.

Not implemented in v0.22.0:

- runtime execution.
- manual smoke execution.
- model/provider calls.
- local runtime provider integrations.
- remote execution or remote worker dispatch.
- mobile sensor access.
- plugin enablement.
- OpenWebUI integration or configuration.
- scanner runtime.
- Skill Factory or self-improvement.
- production persistence.
- dependencies.
- production Control Center authority.
