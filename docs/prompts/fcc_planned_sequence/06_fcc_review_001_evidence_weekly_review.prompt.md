# FCC-REVIEW-001 Evidence Narrative And Weekly CEO Review

Role: You are a Principal Software Engineer implementing a read-only review and
evidence narrative lane.

Task: Make Evidence read like history and Weekly Review summarize decisions,
memory changes, CRM movement, drafts, blockers, and next-week priorities.

Requirements:
- Weekly summaries must distinguish completed, deferred, rejected, blocked,
  stale, planned, and missing-source states.
- Evidence must answer what was proposed, decided, changed, denied, skipped,
  corrected, blocked, and what remains reversible/safe-disabled.
- Use safe refs, redacted summaries, and backend-owned/read-only projections.
- Do not make raw JSON the primary UI.

Non-goals:
- No automatic weekly generation by model/provider, no connector writes, no
  external sends, no memory writes beyond already accepted reviewed-memory
  routes, no context injection, no background jobs, and no production authority.

Focused checks:
- `make frontend-check`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py tests/test_fcc_v1_006_evidence_timeline_productization.py -q`
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `git diff --check`
