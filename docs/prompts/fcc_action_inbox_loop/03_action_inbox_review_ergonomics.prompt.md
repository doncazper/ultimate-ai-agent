# FCC-ACTION-INBOX-LOOP-001c Action Inbox Review Ergonomics

Role: You are a Principal Software Engineer implementing a focused Control
Center readability improvement.

Task: Add Action Inbox filters/drilldowns for the six backend-classified lanes:
- `ready_for_decision`
- `approved_local_task_lane`
- `blocked_by_authority`
- `expired_stale`
- `receipt_recorded`
- `proposal_only_no_execution_path`

Scope:
- This is presentation-only filtering and drilldown over backend/API lane data.
- Do not add runtime authority or new mutating controls.
- Do not make raw JSON the primary operator UI.
- Do not hide missing, blocked, stale, proposal-only, or mock-only state.

Requirements:
- Filters and drilldowns are driven by backend/API `action_group_id`,
  `action_group_label`, receipt visibility, blocked refs, and safe summaries.
- React may own only presentation state: selected filter, expanded item, search
  text, and collapsed/expanded sections.
- Each filtered view must preserve the approval envelope and receipt visibility
  cards.
- Each lane must show count, reason, available operator action, and blocked
  authority refs where applicable.
- No generic Execute button or broad action wording appears.
- Mock/degraded fallback remains non-authoritative and cannot expose decision
  or commit controls.

Tests:
- Each lane filter renders only matching backend-classified items.
- Drilldown preserves envelope and receipt visibility fields.
- Blocked/proposal/stale lanes show explanation, not mutation controls.
- Receipt-recorded lane shows safe receipt refs.
- Mock/degraded fallback filters still show unavailable/non-authoritative
  states and no decision/commit controls.

Run focused checks:
- `make frontend-check`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `.venv/bin/python scripts/verify_operational_maturity.py`

