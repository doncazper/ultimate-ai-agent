# Foundation Gate Implementation Plan v0.19.1

Status: Current Foundation Gate implementation plan for v0.19.1.

v0.19.1 hardens Foundation Gate coverage for M15 Approval Queue + Receipt/Event Viewer UI safety.

## Skill Package Security Rule

v0.19.1 does not change the Skill Package Security Rule. The web shell may display plugin governance summaries only; it cannot install, enable, configure, or execute plugins or skills.

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
- approval refs are identifiers only and never authority.
- Python Agent Core remains the only approval authority.
- receipt/event detail views are redacted summary metadata only.
- safe mock review data exists.
- forbidden approval execution, receipt mutation, event raw, memory raw, file raw, browser storage, credential field, raw prompt/file/memory/event/receipt/provider, and dangerous control fragments are absent from app implementation files.
- `scripts/verify_control_center_frontend.py` passes.

This gate does not add runtime execution, backend routes, model/provider calls, remote dispatch, mobile sensor access, plugin enablement, native build workflows, or production Control Center authority.
