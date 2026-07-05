# Phase 07: Smart Lists

Branch: `codex/crm-07-smart-lists`

Commit: `Add CRM smart lists`

Goal: Add UAA-native smart lists.

Smart lists:

- Stale promises.
- Warm relationships.
- Needs follow-up.
- High-context contacts.
- Unanswered outreach.
- Opportunity at risk.
- Needs evidence.
- Ready for Action Inbox.
- Blocked external sync.
- Recently changed.

Implement:

- Backend smart list contracts.
- Deterministic membership rules.
- CLI inspection.
- UI smart-list sidebar.

Rules:

- Membership rules must be explainable.
- No hidden context injection.
- No external sync.

Tests:

- smart list rule coverage.
- safe refs only.
- no hidden context injection.
- UI filter/list behavior.

Verification:

- focused backend/frontend tests
- documentation integrity
- `git diff --check`
