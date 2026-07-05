# Phase 01: CRM Product Truth And Competitive Feature Map

Branch: `codex/crm-01-product-truth-feature-map`

Commit: `Add CRM local command center plan`

Goal: Create the durable product plan for UAA CRM: full-strength vision,
repo-safe current slice, blocked authority, promotion path, and feature matrix
inspired by public CRM feature patterns.

Implement:

- `docs/control_center/UAA_CRM_LOCAL_COMMAND_CENTER_PLAN.md`
- `docs/control_center/UAA_CRM_FEATURE_MINE_FOLLOWUPBOSS_WISEAGENT.md`
- Update the smallest relevant docs index and kanban entry without creating a
  competing roadmap.

Must include:

- Full-strength UAA CRM.
- Repo-safe implementation sequence.
- Blocked authority lanes.
- Exact promotion path.
- Public feature-pattern attribution.
- Explicit no-copy boundary for proprietary app assets, code, UI, copy,
  templates, screenshots, private schemas, private data, or branding.

Verification:

- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `.venv/bin/python scripts/verify_product_truth.py`
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `git diff --check`
