# Approval Receipt UI Safety

Status: Active for v0.19.0 / M15 Approval Queue + Receipt/Event Viewer UI.

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

Forbidden data handling:

- no raw secrets.
- no raw prompt bodies.
- no raw file bodies.
- no raw memory contents.
- no raw credentials.
- no provider payloads.
- no sensitive browser storage.
- no cookies or browser credential APIs.
- no analytics, auth, SaaS SDKs, model/provider SDKs, browser automation, mobile sensor APIs, native build tooling, or plugin enablement.

The static verifier `scripts/verify_control_center_frontend.py` checks the frontend implementation for dangerous M15 endpoint strings, dangerous action button labels, sensitive browser APIs, unsafe dependencies, secret-like fixtures, generated artifacts, and unsafe API base policy drift.

Foundation Gate criterion `m15_approval_receipt_event_ui_safe` verifies that the M15 UI files exist, routes are present, read-only/preview-only and redacted summary markers are visible, forbidden M15 mutation/control fragments are absent from app implementation files, and the static frontend safety verifier passes.

This patch adds no approval execution, no approve/reject mutation route, no receipt mutation route, no event mutation route, no backend route, no runtime execution, no model/provider call, no remote dispatch, no mobile sensor access, no plugin enablement, no native build workflow, and no production Control Center authority.
