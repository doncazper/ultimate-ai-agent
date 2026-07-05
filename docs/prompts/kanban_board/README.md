# Kanban Board Prompt Bundle

Status: Stored execution prompts for the UAA Work Board / Kanban cockpit.

Purpose: Give operators a scoped, repeatable prompt sequence for implementing
and hardening the backend-owned Work Board while preserving UAA authority
invariants.

These prompts are operator-run instructions, not runtime system prompts. They do
not grant authority by themselves and do not replace `AGENTS.md`,
`docs/control_center/OPERATOR_SHELL_GAP_MAP.md`,
`docs/control_center/release_surface_manifest.json`, or
`docs/control_center/route_status_manifest.json`.

## Prompt Order

1. `01_work_board_read_model_and_cli.prompt.md`
2. `02_work_board_ui_interactions.prompt.md`
3. `03_work_board_verification_and_docs.prompt.md`

Use `00_execute_kanban_board_end_to_end.prompt.md` for an end-to-end run.

## Authority Boundary

This bundle keeps the Work Board read-only and local-first unless a later
accepted authority lane explicitly promotes durable board mutation. It does not
grant connector writes, issue tracker writes, provider/model calls,
shell/subprocess execution, browser automation inside UAA runtime, background
autonomy, public beta, public release, production readiness, or production
authority.

React may own presentation state such as selected view, filters, expanded
details, and unsaved drag/drop preview. Python Agent Core/API/CLI must own
durable board truth, safe refs, blocked authority posture, proof refs, evidence
refs, and promotion-path refs.
