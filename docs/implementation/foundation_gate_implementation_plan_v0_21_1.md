# Foundation Gate Implementation Plan v0.21.1

Status: Historical Foundation Gate implementation plan for v0.21.1.

v0.21.1 adds Foundation Gate coverage for M17 Evidence/File/Memory Viewer safety hardening.

## Skill Package Security Rule

v0.21.1 does not change the Skill Package Security Rule. The web shell may display plugin governance summaries only; it cannot install, enable, configure, or execute plugins or skills.

All skills are untrusted packages by default until a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities exist.

Criteria:

- `m17_evidence_file_memory_viewer_safe`
- `m17_evidence_file_memory_viewer_hardening_safe`

Evaluator:

- `FoundationGateEvaluator.check_m17_evidence_file_memory_viewer_safe`
- `FoundationGateEvaluator.check_m17_evidence_file_memory_viewer_hardening_safe`

The v0.21.1 hardening evaluator checks:

- alternate safe mock refs exist for evidence, file ref, and memory summaries.
- selected M17 summary cards expose accessible selected-state reviewability.
- frontend tests cover alternate M17 metadata selection while read-only and redacted summary-only.
- static frontend verifier checks M17 hardening mock markers and selected-state markers.
- docs describe the hardening patch, browser smoke reviewability, no backend API route, and unchanged OpenAPI path count.
- OpenAPI path count remains `74`.
- backend evidence/raw, file write/delete/content, filesystem browse, and memory raw/write/delete/learn/forget routes are absent.
- `scripts/verify_control_center_frontend.py` passes.

This gate does not add M18, runtime execution, backend routes, model/provider calls, remote dispatch, mobile sensor access, plugin enablement, native build workflows, raw payload display, auth, cookies, analytics, SaaS SDKs, dependencies, or production Control Center authority.
