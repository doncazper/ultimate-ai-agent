# FCC-INBOX-001 Deeper Action Inbox / Approval Envelope UX

Role: You are a Principal Software Engineer implementing a focused Action
Inbox product-readability lane.

Task: Deepen the Action Inbox approval-envelope UX without adding broad action
authority.

Read first:
- `AGENTS.md`
- `docs/kanban/founder_command_center_board.md`
- `docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md`
- `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`
- Action Inbox backend/API/frontend/storage/tests

Requirements:
- The active Action Inbox must make envelope kind, exact scope, risk,
  side-effect class, approval requirement, expiry/staleness, evidence refs,
  idempotency posture, expected receipts, receipt visibility,
  rollback/safe-disable posture, blocked authority, replay posture, and
  conflict posture easy to scan.
- Use backend/API read models for product truth. React may own only selected
  lane, expanded item, search/filter text, and other presentation state.
- `/inbox` and `/actions` mapping must be clear without breaking route/API
  tests.
- Mock/degraded fallback must remain non-authoritative.

Non-goals:
- No generic Execute button, connector writes, shell/subprocess execution,
  provider/model authority, memory writes, context injection, browser
  automation, plugin runtime import, remote execution, production/public claims,
  or maturity rank promotion unless already supported by manifest/verifier.

Focused checks:
- `make frontend-check`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q`
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `.venv/bin/python scripts/verify_control_center_frontend.py`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `git diff --check`
