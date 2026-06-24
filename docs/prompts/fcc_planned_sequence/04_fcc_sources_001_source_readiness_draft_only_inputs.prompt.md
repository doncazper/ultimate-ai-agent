# FCC-SOURCES-001 Source Readiness And Draft-Only Inputs

Role: You are a Principal Software Engineer implementing a read-only source
readiness product lane.

Task: Make inbox, calendar, tasks, CRM-lite/manual notes, repo, and local-file
readiness visible with metadata-only and manual/draft-only posture.

Requirements:
- Prefer the dedicated backend-owned source readiness route when available.
- Show supported states: ready, blocked, missing, metadata_only, unavailable,
  and not_configured.
- Draft-only inputs must be review/proposal envelopes, not connector writes.
- Missing contracts and blocked authorities must be visible.
- React must not invent source readiness, connector state, account state,
  source evidence, or maturity rank.

Non-goals:
- No account auth, background polling, raw body ingestion, attachment download,
  send/write/archive/delete/label/move, calendar write, connector runtime,
  provider/model calls, memory writes, context injection, shell/subprocess
  execution, browser automation, or production authority.

Focused checks:
- `make frontend-check`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `git diff --check`
