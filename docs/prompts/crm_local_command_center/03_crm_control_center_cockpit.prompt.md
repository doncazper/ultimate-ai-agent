# Phase 03: CRM Control Center Cockpit

Branch: `codex/crm-03-control-center-cockpit`

Commit: `Build CRM cockpit from backend read model`

Goal: Replace the fixture-only CRM shell with a UAA-native CRM cockpit rendered
from backend read models.

UI:

- CRM overview.
- Relationship list.
- Selected relationship inspector.
- Timeline panel.
- Follow-up queue.
- Pipeline board.
- Smart lists.
- Proof/evidence panel.
- Blocked authority panel.

Design:

- Desktop command-center aesthetic.
- Dense, scannable, Apple-grade.
- No marketing hero.
- No raw JSON for critical workflows.
- Every blocked control visibly blocked.
- Fallback data must be visibly non-authoritative.

Tests:

- `/crm` renders from backend-owned data.
- fixture/mock fallback is visibly non-authoritative.
- no mutation controls execute.
- blocked external/sending lanes remain blocked.
- route transitions, tabs, filters, and inspectors work.

Verification:

- focused frontend tests
- `make frontend-check`
- visual check if baseline/manifests changed
- release-surface verifier
- `git diff --check`
