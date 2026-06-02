# Approval Receipt UI Safety

Status: Active for v0.21.1; M15 Approval Queue + Receipt/Event Viewer UI remains read-only and M16/M17 surfaces are separate.

M15 safety boundary:

- read-only.
- preview-only.
- summary-only.
- redacted.
- visibly mock when using frontend fallback data.
- non-authoritative.
- backed by static frontend safety verification and Foundation Gate coverage.

Forbidden UI controls and endpoints:

- no approval execution controls.
- no grant/reject mutation controls.
- no send, write, publish, run, deploy, enable, install, or mutation controls.
- no `/approvals/approve`, `/approvals/deny`, `/control-center/approvals/execute`, `/control-center/approvals/approve`, `/control-center/approvals/deny`, `/receipts/delete`, `/events/raw`, `/memory/raw`, or `/files/raw` frontend targets.
- no backend authority bypass.
- no arbitrary approval ref authority.
- no production Control Center authority.

Required safety copy:

- the UI cannot grant, deny, execute, or bypass approvals.
- approval refs are identifiers only and never authority.
- Python Agent Core remains the only approval authority.
- receipt detail is redacted summary metadata only.
- event detail is redacted summary metadata only.

Forbidden data handling:

- no raw secrets.
- no raw prompt bodies.
- no raw file bodies.
- no raw memory contents.
- no raw credentials.
- no raw event payloads.
- no raw receipt payloads.
- no provider payloads.
- no raw M15 review fields.
- no credential-like review fields.
- no sensitive browser storage.
- no cookies or browser credential APIs.
- no analytics, auth, SaaS SDKs, model/provider SDKs, browser automation, mobile sensor APIs, native build tooling, or plugin enablement.

The static verifier `scripts/verify_control_center_frontend.py` checks the frontend implementation for dangerous M15 endpoint strings, dangerous action button labels, authority-boundary copy, raw M15 review fields, credential-like review fields, sensitive browser APIs, unsafe dependencies, secret-like fixtures, generated artifacts, and unsafe API base policy drift.

Foundation Gate criterion `m15_approval_receipt_event_ui_safe` verifies that the M15 UI files exist, routes are present, read-only/preview-only and redacted summary markers are visible, authority-boundary copy is present, forbidden M15 mutation/control/raw-field fragments are absent from app implementation files, and the static frontend safety verifier passes.

This patch adds no M16 Event Timeline + Run/Receipt Trace Viewer, no approval execution, no approve/reject mutation route, no receipt mutation route, no event mutation route, no backend route, no OpenAPI path count change, no runtime execution, no model/provider call, no remote dispatch, no mobile sensor access, no plugin enablement, no dependency, no native build workflow, and no production Control Center authority.
