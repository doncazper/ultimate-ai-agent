# FCC-ACTION-INBOX-LOOP-001d Morning Briefing Source Readiness

Role: You are a Principal Software Engineer implementing a read-only Founder
Command Center product-readability lane.

Task: Improve Morning Briefing/source readiness using backend-owned or
contract-owned read-only metadata. Keep this proposal/read-only only.

Scope:
- No connector writes.
- No email/calendar reads unless an existing backend read-only contract already
  supports safe metadata.
- No account auth, credential handling, background refresh, notifications,
  message send/archive/delete/label/move, calendar write, provider/model call,
  memory write, context injection, shell/subprocess execution, browser
  automation, plugin runtime import, remote execution, public beta/release
  claim, production authority, or maturity rank promotion.

Requirements:
- Morning Briefing should show clear read-only source readiness for available
  safe refs and explicit blockers for missing contracts.
- Use existing backend/API summary fields first. Add only read-only classifier
  fields if the backend lacks a stable source-readiness shape.
- Distinguish:
  - implemented read-only source metadata
  - contract-only planned source metadata
  - mock/degraded fallback
  - blocked connector/account/runtime authority
  - stale or unavailable source posture
- Surface next safe action and missing contract refs.
- Do not render draft/send/write controls.

Tests:
- Morning Briefing shows source readiness and blocked source contracts.
- Mock/degraded fallback is non-authoritative.
- No connector write, send, sync, provider/model, memory write, context
  injection, shell/subprocess, browser automation, or production controls appear.
- Docs and product language remain aligned.

Run focused checks:
- `make frontend-check`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `.venv/bin/python scripts/verify_operational_maturity.py`

