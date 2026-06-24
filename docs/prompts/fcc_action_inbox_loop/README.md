# FCC Action Inbox Loop Prompt Bundle

Status: Stored execution prompts for the next Founder Command Center Action
Inbox and Morning Briefing readability loop. These prompts are operator-run
instructions, not runtime system prompts.

Purpose: Move from the Action Inbox truth-binding fix through the next exact
`local_task_create` review gate, receipt refresh/reconciliation, Action Inbox
review ergonomics, and read-only Morning Briefing source readiness without
adding broader authority.

## Prompt Order

1. `01_local_task_create_graduation_gate_review.prompt.md`
2. `02_local_task_receipt_refresh_reconciliation.prompt.md`
3. `03_action_inbox_review_ergonomics.prompt.md`
4. `04_morning_briefing_source_readiness.prompt.md`
5. `05_recommended_next_local_task_create_gate.prompt.md`
6. `06_execute_next_planned_steps.prompt.md`
7. `07_recommended_next_safe_disable_ui_followup.prompt.md`
8. `08_source_readiness_dedicated_route.prompt.md`

Use `00_execute_all_review_verify_harden.prompt.md` when the operator wants one
end-to-end run through the full sequence.

Use `06_execute_next_planned_steps.prompt.md` when the operator wants the next
planned sequence: gate review, exact safe-disable/rollback posture for
`local_task_create`, Action Inbox review polish, read-only Morning Briefing
source readiness, verification, and finalization.

Use `07_recommended_next_safe_disable_ui_followup.prompt.md` when the operator
wants the active Action Inbox UI to display backend-owned local task posture
without adding authority.

Use `08_source_readiness_dedicated_route.prompt.md` when the operator wants to
promote embedded Morning Briefing source readiness into a dedicated, typed,
read-only backend route without pretending live connectors exist.

## Authority Boundary

This bundle does not grant generic execution, connector writes,
shell/subprocess execution, provider/model authority, memory writes, context
injection, browser automation, remote execution, plugin runtime import,
production-readiness claims, maturity rank promotion, or new route authority.

The only existing local mutation in scope is the already-approved
`local_task_create` micro-lane. All later work in this bundle is review,
readability, refresh/reconciliation, filtering, drilldown, or read-only source
metadata.
