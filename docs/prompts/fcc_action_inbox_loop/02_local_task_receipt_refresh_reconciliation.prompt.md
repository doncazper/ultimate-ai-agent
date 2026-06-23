# FCC-ACTION-INBOX-LOOP-001b Local Task Receipt Refresh/Reconciliation

Role: You are a Principal Software Engineer implementing production-grade
receipt visibility hardening.

Task: After a successful `local_task_create` commit from `/actions`, refresh or
reconcile the Action Inbox from backend/API data so the card moves from
pending/eligible to receipt-recorded truth without UI-only success state.

Scope:
- Keep the existing typed `local_task_create` commit route and backend storage
  semantics.
- Do not add new route authority.
- Do not add generic execution, connector writes, shell/subprocess execution,
  provider/model authority, memory writes, context injection, browser
  automation, plugin runtime import, remote execution, public beta/release
  claims, production authority, or maturity rank promotion.

Requirements:
- A successful commit must trigger a backend-owned read refresh or a narrow
  reconciliation path that uses only the returned receipt plus backend/API
  read-model fields.
- The visible card must show safe refs for:
  - `local_task_ref`
  - `local_task_commit_receipt_ref`
  - Evidence Timeline event ref
  - replay posture
  - conflict posture
- The item must no longer display an eligible commit control after the commit
  receipt is present.
- Missing or failed refresh must render explicit safe states such as
  `refresh_pending`, `refresh_failed`, `backend_read_model_unavailable`, or
  `receipt_ref_pending_backend_refresh`.
- React must not invent approval, eligibility, receipt truth, replay posture,
  conflict posture, exact scope, side-effect class, risk, or authority.
- Backend/API data remains the source of truth for persisted committed state.

Tests:
- Successful commit re-fetches or reconciles `/actions` so committed safe refs
  appear on the card.
- Commit control disappears after receipt visibility indicates committed state.
- Refresh failure keeps receipt result visible as pending backend refresh, not
  as final backend-owned read-model truth.
- Duplicate replay displays replay posture from backend/API data.
- Conflict rejection displays safe failure and does not mutate UI into a
  committed state.
- React request body sends no grants, authority scopes, risk, side-effect
  class, approval requirement, exact scope, raw prompt/log/path, credentials, or
  secret-like values.

Run focused checks:
- `make frontend-check`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_founder_loop_storage.py -q`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
- `.venv/bin/python scripts/verify_documentation_integrity.py`

