# FCC-BRIEFING-001 Morning Briefing And Today Plan V1

Status: Implemented
Baseline: v0.104.0 / 0.104.0
Primary surfaces: `/briefing` and `/today`

## Purpose

FCC-BRIEFING-001 makes Morning Briefing the read-only daily home for the
Founder Command Center and keeps Today as the decision view. It composes
priorities, commitments, memory hints, blocked sources, source-readiness
posture, review queue state, CRM-lite follow-ups, dogfood signals, weekly
review narrative refs, and next safe actions from backend-owned safe refs.

This is a daily-loop readability lane. It is not a connector, refresh,
notification, account-auth, source-ingestion, model/provider, memory-write, or
execution lane.

## Implementation Evidence

- Backend route: `GET /control-center/morning-briefing/summary`.
- Related source-readiness route: `GET /control-center/sources/readiness`.
- Today read model: `GET /control-center/today/summary`.
- Storage/source: `src/ultimate_ai_agent/core/storage/founder_loop.py`.
- API route owner: `src/ultimate_ai_agent/api/founder_loop.py`.
- Frontend route: `/briefing` renders
  `apps/control-center/src/components/FounderLoopPanels.tsx::MorningBriefingPanel`.
- Frontend type:
  `apps/control-center/src/api/types.ts::FounderLoopMorningBriefing`.
- Verification:
  `scripts/verify_fcc_briefing_001_morning_briefing_today_plan.py`,
  `tests/test_fcc_briefing_001_morning_briefing_today_plan.py`,
  `tests/test_founder_loop_storage_briefing.py`,
  `tests/test_control_center_api_routes.py`, and
  `apps/control-center/src/App.test.tsx`.

## Current Truth

Morning Briefing exposes:

- `daily_loop_summary` with Morning Briefing as home surface and Today as
  decision surface.
- `daily_loop_sections` for Today priorities, blocked/missing sources,
  CRM-lite follow-ups, memory why-shown, review queue summary, and dogfood
  capture.
- `source_readiness_posture` and `source_readiness_items` with supported states
  for `ready`, `blocked`, `missing`, `metadata_only`, `unavailable`, and
  `not_configured`.
- `review_queue_groups`, `crm_lite_followups`, `memory_why_shown_items`,
  `weekly_review_narrative`, and `dogfood_capture`.
- Briefing items with source refs, evidence refs, memory refs where available,
  or explicit missing-source/blocked posture.
- `next_safe_action` values that point to review or contract work instead of
  unscoped source reads or execution.

## Authority Boundary

Morning Briefing is bounded preview/read-only state. It does not add email or
calendar fetch, account auth, background refresh, notification delivery,
connector runtime/write, raw source ingestion, provider/model calls, memory
writes, context injection, shell/subprocess execution, browser automation,
public beta, public distribution, production authority, or action execution.

The UI must not render refresh, notification, connector, send, write, or
execution controls unless a later accepted milestone grants the exact
capability with tests, approval boundaries, evidence, and rollback/safe-disable
posture.

## Verification Commands

```bash
.venv/bin/python scripts/verify_fcc_briefing_001_morning_briefing_today_plan.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_fcc_briefing_001_morning_briefing_today_plan.py tests/test_founder_loop_storage_briefing.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
.venv/bin/python scripts/verify_operational_maturity.py
.venv/bin/python scripts/verify_documentation_integrity.py
make frontend-check
git diff --check
```
