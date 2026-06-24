# FCC-BRIEFING-001 Morning Briefing And Today Plan V1

Role: You are a Principal Software Engineer implementing a read-only daily-loop
product slice.

Task: Make Morning Briefing and Today Plan V1 the first operating surface over
priorities, commitments, memory hints, blocked sources, review queue state, and
next safe actions.

Requirements:
- Every surfaced item must have source/evidence/memory refs or an explicit
  missing-source/blocked posture.
- Use backend-owned summaries first. Add only read-only backend fields if the
  current contract lacks required safe refs.
- Distinguish implemented, contract-only, planned, mock/degraded, stale,
  unavailable, and blocked states.
- Do not render refresh, notification, connector, send, write, or execution
  controls unless a later accepted milestone authorizes them.

Non-goals:
- No email/calendar fetch, account auth, background refresh, notification
  delivery, connector runtime/write, provider/model calls, memory writes,
  context injection, shell/subprocess execution, browser automation, or
  production authority.

Focused checks:
- `make frontend-check`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `git diff --check`
