# Foundation Gate Implementation Plan v0.19.0

Status: Current Foundation Gate implementation plan for v0.19.0.

v0.19.0 adds Foundation Gate coverage for M15 Approval Queue + Receipt/Event Viewer UI.

## Skill Package Security Rule

v0.19.0 does not change the Skill Package Security Rule. The web shell may display plugin governance summaries only; it cannot install, enable, configure, or execute plugins or skills.

All skills are untrusted packages by default until a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities exist.

Criterion:

- `m15_approval_receipt_event_ui_safe`

Evaluator:

- `FoundationGateEvaluator.check_m15_approval_receipt_event_ui_safe`

The evaluator checks:

- M15 UI component files exist.
- `/approvals`, `/receipts`, and `/events` frontend routes are present.
- Approval Queue, Receipt Viewer, and Event Viewer headings are present.
- read-only and preview-only markers are present.
- Approval Authority boundary copy is present.
- redacted summary-only markers are present.
- safe mock review data exists.
- forbidden approval execution, receipt mutation, event raw, memory raw, file raw, browser storage, cookie, and credential field fragments are absent from app implementation files.
- `scripts/verify_control_center_frontend.py` passes.

This gate does not add runtime execution, backend routes, model/provider calls, remote dispatch, mobile sensor access, plugin enablement, native build workflows, or production Control Center authority.
