# Foundation Gate Implementation Plan v0.20.1

Status: Current Foundation Gate implementation plan for v0.20.1.

v0.20.1 hardens Foundation Gate coverage for M16 Event Timeline + Run/Receipt Trace Viewer safety.

## Skill Package Security Rule

v0.20.1 does not change the Skill Package Security Rule. The web shell may display plugin governance summaries only; it cannot install, enable, configure, or execute plugins or skills.

All skills are untrusted packages by default until a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities exist.

Criterion:

- `m16_event_timeline_trace_viewer_safe`

Evaluator:

- `FoundationGateEvaluator.check_m16_event_timeline_trace_viewer_safe`

The evaluator checks:

- M16 timeline and trace UI component files exist.
- `/events/timeline` frontend route is present.
- Event Timeline heading and M16 trace surface copy are present.
- timeline and trace views are read-only.
- selected trace detail is redacted summary metadata only.
- trace export and external telemetry are unavailable.
- safe mock event, run, correlation, receipt, relation, and Foundation Gate evidence refs exist.
- raw prompt, file, memory, event, receipt, provider, secret, and credential-like trace fields are rejected.
- execution, export, approval mutation, tool execution, runtime execution, remote dispatch, browser storage, credential field, and dangerous control fragments are absent from app implementation files.
- OpenAPI path count remains `74`.
- backend timeline, trace, raw event, and telemetry export routes are absent.
- generated Control Center build and log artifacts remain untracked.
- `scripts/verify_control_center_frontend.py` passes.
- docs for the Event Timeline UI, Run Receipt Trace Viewer, and Trace Redaction Policy exist.

This gate does not add runtime execution, backend routes, model/provider calls, remote dispatch, mobile sensor access, plugin enablement, native build workflows, external telemetry export, raw payload display, or production Control Center authority.
