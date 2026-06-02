# Runtime Smoke UI Safety

Status: Active for v0.22.0 / M18.

M18 keeps local runtime and manual smoke UI surfaces safe by treating them as control/status summaries, not runtime controls.

Required controls:

- `/runtime/local` must remain read-only.
- `/runtime/manual-smoke` must remain validation-only.
- M18 mock data must be visibly mock, non-authoritative, and redacted summary-only.
- The frontend may reference `GET /runtime/readiness`, `GET /runtime/capability-matrix`, and `POST /runtime/smoke-reports/validate`.
- The frontend must not reference runtime execute, smoke execute, start, stop, connect, launch, provider invoke, remote dispatch, mobile sensor, plugin enablement, or native build endpoints.

Forbidden display:

- no raw smoke report.
- no raw prompts.
- no raw response bodies.
- no raw transcripts.
- no raw file contents.
- no raw memory contents.
- no credentials.
- no provider payloads.
- no secret-like endpoint query values.

Forbidden behavior:

- no runtime execution.
- no manual smoke execution.
- no model/provider calls.
- no external telemetry export.
- no production readiness claim.
- no production Control Center authority.

Verification:

- `scripts/verify_control_center_frontend.py` rejects M18 execution endpoints, dangerous runtime/smoke control labels, raw smoke fields, and credential-like report fields.
- Foundation Gate criterion `m18_local_runtime_manual_smoke_surface_safe` checks the M18 UI files, docs, frontend verifier, and unchanged OpenAPI path count.
