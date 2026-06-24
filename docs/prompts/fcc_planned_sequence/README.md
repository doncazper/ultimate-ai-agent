# Founder Command Center Planned Sequence Prompt Bundle

Status: Stored execution prompts for the next planned Founder Command Center
sequence.

Purpose: Give operators a scoped, repeatable prompt sequence for UAA-P1-066 and
the next FCC product lanes while preserving repository truth and safety
boundaries.

These prompts are operator-run instructions, not runtime system prompts. They do
not grant authority by themselves and do not replace `AGENTS.md`,
`docs/kanban/current_board.md`, `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`,
or the operational maturity manifest.

## Prompt Order

1. `01_uaa_p1_066_local_model_manager_read_only_status.prompt.md`
2. `02_fcc_inbox_001_deeper_approval_envelope_ux.prompt.md`
3. `03_fcc_briefing_001_morning_briefing_today_plan.prompt.md`
4. `04_fcc_sources_001_source_readiness_draft_only_inputs.prompt.md`
5. `05_fcc_memory_crm_001_professional_memory_crm_binding.prompt.md`
6. `06_fcc_review_001_evidence_weekly_review.prompt.md`
7. `07_fcc_health_001_self_healing_recommendations.prompt.md`
8. `08_fcc_dogfood_001_fourteen_day_private_harness.prompt.md`
9. `09_fcc_action_001_approval_bound_local_micro_lanes.prompt.md`
10. `10_fcc_polish_001_native_apple_grade_ux.prompt.md`

Use `00_execute_all_review_verify_finalize.prompt.md` for an end-to-end run.

## Global Authority Boundary

Unless a specific future prompt has an already accepted scoped milestone and
all gates pass, this bundle does not add generic execution, connector writes,
shell/subprocess execution, browser automation, model/provider authority,
memory writes, context injection, plugin runtime import, remote execution,
public beta, public distribution, production readiness, or production
authority.

Python Agent Core remains the source of product truth. Control Center may render
backend-owned state and presentation-only filters; React must not mint
eligibility, approval, receipt, source, memory, route, model, or maturity truth.
