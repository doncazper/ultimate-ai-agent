# FCC-MEMORY-CRM-001 Professional Memory And CRM-lite Binding

Role: You are a Principal Software Engineer implementing a governed memory and
CRM-lite readability lane.

Task: Bind reviewed professional memory to people, organizations,
opportunities, commitments, stale follow-ups, draft opportunities, and
relationship health while preserving memory as recall, not truth or authority.

Requirements:
- Every memory-derived item must show provenance and "why shown" evidence.
- Distinguish reviewed recall, candidates, conflicts, stale memory, draft
  opportunity, blocked source, and missing evidence.
- Use backend-owned memory/review/source refs. React may render/filter only.
- CRM-lite bindings must be local/read-only/proposal-only unless a later exact
  connector or local mutation lane is accepted.

Non-goals:
- No automatic memory truth, hidden context injection, external CRM writes,
  account sync, connector writes, model/provider calls, background sync,
  memory delete/export execution, or production authority.

Focused checks:
- `make frontend-check`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py tests/test_founder_loop_storage_safety.py -q`
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `git diff --check`
