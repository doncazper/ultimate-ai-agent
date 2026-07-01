# FCC-LOOP-002 Founder Loop Ergonomics Pass

Status: implemented as a Control Center UI/readability lane.

## Goal

Make the daily founder/operator loop obvious without adding runtime authority:

1. What matters today.
2. What needs approval or review.
3. What plans or actions are waiting.
4. What memory and evidence are influencing the loop.
5. What is blocked or unsafe.

## Implemented Surface Changes

- Today now opens with a compact daily-loop command deck that groups the loop
  into Today, Review, Waiting, Influence, and Blocked cards.
- The shared Founder Loop spine includes Briefing alongside Today, Source Inbox,
  Plans, Action Inbox, Memory, Evidence, and Settings.
- Action Inbox now starts with an operator overview of grouped review work,
  proposal-only posture, blocked authority refs, and receipt-backed decisions.
- Briefing now has an operator summary that names the starting point for the
  local loop, source readiness posture, review receipts, and safe next action.
- Memory now has a "Memory in today's loop" summary before the workbench
  internals, including recall influence, affected surfaces, and blocked context
  authority.
- Evidence now has a loop proof summary that connects route-surface events,
  blocked states, and weekly review proof to the daily loop.
- Proposal-only and receipt language was tightened so controls describe receipt
  recording or exact local-task commit receipts instead of broad apply, use, or
  execute authority.

## Safety Boundaries

This lane does not add:

- backend routes or OpenAPI surface
- action execution
- workflow execution
- model or provider calls
- connector writes
- web fetching or browser automation
- shell or subprocess execution
- memory writes or hidden memory maintenance
- context injection or hidden context pack use
- production, public beta, or public release claims

Existing receipt-backed and approval-bound controls remain the only mutating
posture visible in the affected surfaces. Proposal-only artifacts stay review
artifacts until a later exact milestone grants additional authority.

## Verification Focus

Focused frontend coverage checks:

- the daily-loop command deck renders on Today
- Briefing appears in the shared loop spine
- Action Inbox, Briefing, Memory, and Evidence show grouped operator summaries
- proposal-only and blocked authority language is visible
- fallback states remain non-authoritative
- raw JSON is not the primary UI
- proposal-only artifacts do not expose apply, use, or execute controls

The implementation reuses existing backend read models and mock fallback data.
Any future deeper loop wiring should remain backend-owned, receipt-backed,
redacted, and separately scoped.
