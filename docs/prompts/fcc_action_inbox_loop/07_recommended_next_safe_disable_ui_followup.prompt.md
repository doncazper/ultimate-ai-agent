# FCC Action Inbox Next Step 07 - Safe-Disable Posture UI Follow-Up

You are working in the repository root for this workspace.

Read and follow:

- `AGENTS.md`
- `docs/prompts/fcc_action_inbox_loop/06_execute_next_planned_steps.prompt.md`
- `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`
- `docs/control_center/operational_maturity_manifest.json`

Task:

Polish the active Action Inbox product screen so the backend-owned
`local_task_create` safe-disable/rollback posture is visible in the review
inspector without adding any authority.

Scope:

1. Inspect the active `/actions` route and confirm which component renders it.
2. Add a compact "Local task commit posture" section/card to the active Action
   Inbox inspector.
3. Render only backend-owned fields already returned by
   `GET /control-center/actions/inbox`, including:
   - `local_task_commit_eligible`
   - `local_task_commit_approval_status`
   - `local_task_commit_approval_ref`
   - `local_task_commit_contract_ref`
   - `local_task_commit_route_ref`
   - `local_task_commit_next_safe_action`
   - `local_task_commit_blocked_reasons`
   - `local_task_commit_external_authority_blocked_refs`
   - `local_task_safe_disable_posture`
   - `local_task_safe_disable_active`
   - `local_task_safe_disable_posture_ref`
   - `local_task_rollback_ref`
   - `local_task_rollback_execution_enabled`
   - `local_task_rollback_blocker_refs`
4. Add or update focused frontend tests proving:
   - commit controls still appear only for eligible approved `local_task_create`
     items;
   - disabled posture remains visible;
   - blocked external authority refs remain visible;
   - React does not send grant lists or authority scopes;
   - no generic Execute button appears.
5. Run focused frontend checks and any affected backend checks.

Non-goals:

- Do not add generic execution.
- Do not add connector writes.
- Do not add shell/subprocess execution.
- Do not add browser automation.
- Do not add provider/model authority.
- Do not add memory writes.
- Do not add context injection.
- Do not add plugin runtime import.
- Do not add remote execution.
- Do not add production/public release claims.
- Do not add new backend routes or broader route authority.

Definition of done:

- The active Action Inbox UI visibly explains why a local task can or cannot be
  committed from backend-owned posture.
- Existing backend eligibility remains the only source of commit-control truth.
- Tests prove no React-minted approval grants, authority scopes, or generic
  execution controls were added.
- Final response lists files changed, verification commands, skipped checks,
  and remaining risks.
