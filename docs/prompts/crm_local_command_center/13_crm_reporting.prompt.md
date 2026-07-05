# Phase 13: Reporting And Accountability

Branch: `codex/crm-13-reporting`

Commit: `Add CRM reporting cockpit`

Goal: Build local CRM reports that matter.

Reports:

- follow-up debt.
- stale promises.
- relationship health.
- opportunity aging.
- source/ref effectiveness.
- activity completion.
- pipeline value.
- blocked authority report.
- memory/evidence coverage.

UI:

- Report cards.
- timeline trend.
- smart-list drilldown.
- proof links.

Rules:

- No fake revenue claims.
- No external sync claims.
- Reports must expose data freshness and missing evidence.

Tests:

- reporting read model.
- UI render.
- no fake revenue claims.
- no external sync claims.

Verification:

- focused backend/frontend tests
- product truth verifier
- `git diff --check`
