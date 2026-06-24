# FCC-REVIEW-001 Evidence Narrative And Weekly CEO Review

Status: Implemented
Baseline: v0.104.0 / 0.104.0
Primary surfaces: `/evidence`, `/today`, `/briefing`, and `/actions`

## Purpose

FCC-REVIEW-001 makes Evidence read like safe-ref history and makes Weekly
Review summarize the founder loop without becoming truth or authority. The
surface answers what was proposed, decided, changed, denied, skipped,
corrected, blocked, stale, reversible/safe-disabled, and missing-source.

This is a read-only evidence narrative lane. It does not generate weekly
reviews with model/provider authority, send external summaries, write memory
beyond already accepted reviewed-memory routes, inject context, run background
jobs, or grant production authority.

## Implementation Evidence

- Evidence route: `GET /control-center/evidence/timeline`.
- Embedded Weekly Review surfaces: `GET /control-center/today/summary`,
  `GET /control-center/morning-briefing/summary`, and
  `GET /control-center/actions/inbox`.
- Storage/source: `src/ultimate_ai_agent/core/storage/founder_loop.py`.
- Frontend binding:
  `apps/control-center/src/components/FounderLoopPanels.tsx::WeeklyReviewNarrativeCard`.
- Frontend type:
  `apps/control-center/src/api/types.ts::FounderLoopWeeklyReviewNarrative`.
- Verification:
  `scripts/verify_fcc_review_001_evidence_narrative_weekly_review.py`,
  `tests/test_fcc_review_001_evidence_narrative_weekly_review.py`,
  `tests/test_control_center_api_routes.py`, and
  `tests/test_fcc_v1_006_evidence_timeline_productization.py`.

## Current Truth

Evidence Timeline already productizes backend-owned safe-ref history for
Action envelope creation, Action decisions, local-task receipts, Chat
receipts/handoffs, and Memory Review decisions. Each event stays redacted,
safe-ref-only, and read-only.

Weekly Review now distinguishes:

- `completed_refs`
- `deferred_refs`
- `rejected_refs`
- `blocked_refs`
- `stale_refs`
- `planned_refs`
- `missing_source_refs`
- `memory_change_refs`
- `crm_movement_refs`
- `draft_refs`
- `next_week_priority_refs`

Weekly Review also keeps proposed, decided, changed, carry-forward, dogfood,
and evidence refs visible. Empty buckets are allowed, but the bucket names are
part of the read model so missing state cannot collapse into a vague summary.

Evidence Narrative also exposes `review_answer_refs` for the prompt-facing
questions: `proposed`, `decided`, `changed`, `denied`, `skipped`, `corrected`,
`blocked`, and `reversible_safe_disabled`. These are derived refs only, not
new authority or new event types.

## Authority Boundary

FCC-REVIEW-001 does not add automatic weekly generation by model/provider,
connector writes, external sends, memory writes beyond existing reviewed
memory routes, context injection, background jobs, rollback execution, action
execution, public beta, public distribution, production readiness, or
production authority.

Evidence and Weekly Review are read-only projections over backend-owned refs.
They do not make raw JSON the primary operator-critical UI and do not treat
summary text as authority.

## Verification Commands

```bash
.venv/bin/python scripts/verify_fcc_review_001_evidence_narrative_weekly_review.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_fcc_review_001_evidence_narrative_weekly_review.py tests/test_control_center_api_routes.py tests/test_fcc_v1_006_evidence_timeline_productization.py -q
.venv/bin/python scripts/verify_operational_maturity.py
.venv/bin/python scripts/verify_documentation_integrity.py
make frontend-check
git diff --check
```
