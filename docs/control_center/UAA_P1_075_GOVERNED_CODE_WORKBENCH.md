# UAA-P1-075 Governed Code Workbench V1

Status: implemented as a contract, test, verifier, Today-spine, Evidence
Timeline, Control Center metadata shape, and Prompt 01 `/coding` cockpit shell
read model seed.

This milestone makes Code narrower than Goat but better governed. It adds a
repo-local Code proposal contract for safe diff summary refs, validation plan
refs, validation result refs, exact approval requirement refs, expected apply
receipt refs, expected rollback receipt refs, idempotency refs, and Evidence
Timeline history. It does not add apply execution, approval grant capture,
unrestricted shell, subprocess execution, remote execution, broad coding-agent
autonomy, provider SDK calls, web fetching, connector writes, file mutation
runtime, public beta, public distribution, or production authority.

## Coding Cockpit Prompt 01 Shell

Prompt 01 adds the repo-safe Coding Cockpit shell without broad runtime
authority.

Full-strength version:

- UAA Coding becomes a local-first coding command center with chat, workspace
  context, diff and patch review, terminal posture, Git posture, live preview
  posture, proof detail, agent workflow timeline, and multi-agent review.
- Authority profiles eventually distinguish Read Only, Ask Before Changes,
  Approve Safe Local Work For Me, Full Local Workspace Access, and separate
  External / Production Authority.

Repo-safe current version:

- Control Center route: `/coding`.
- Backend routes: `GET /control-center/coding/session`,
  `GET /control-center/coding/context`,
  `GET /control-center/coding/patch-proposal`,
  `GET /control-center/coding/patch-apply-readiness`.
- CLI inspection: `scripts/dev/uaa_coding.py inspect-session`,
  `scripts/dev/uaa_coding.py inspect-context`,
  `scripts/dev/uaa_coding.py inspect-patch-proposal`,
  `scripts/dev/uaa_coding.py inspect-patch-apply-readiness`.
- Python Agent Core owns `CodingCockpitSessionReadModel` and
  `CodingWorkspaceContextReadModel` plus the proposal-only patch read model;
  Control Center renders the read models and mock fallback only.
- The shell shows workspace/context, task timeline, diff preview, proof preview,
  agent thread, terminal preview, Git preview, test output preview, live preview,
  authority mode selector, read-only context-pack preview, proposal-only patch
  refs, blocked apply-readiness refs, and blocked authority refs.
- Mock fallback is visibly non-authoritative and grants no workflow truth.

Blocked / needs authority:

- File writes, patch apply, shell/subprocess execution, Git mutation,
  provider/model calls, browser automation, connector writes, background coding
  agents, production authority, public beta, public release, and broad runtime
  authority remain blocked.
- Prompt 01 stores safe refs and bounded summaries only. It does not persist raw
  prompts, raw responses, raw provider payloads, local paths, shell output,
  credentials, tokens, cookies, account identifiers, or private data.

Exact promotion path:

- Prompt 02 graduates backend-owned context-pack preview contracts and
  inspection parity from safe refs only.
- Prompt 03 adds patch proposal artifacts without apply.
- Prompt 04 adds patch apply readiness and blocker refs without apply.
- Later approved lanes add exact patch apply, allowlisted test commands, Git
  review, live preview status, and multi-agent review only after scoped
  approval binding, receipts, rollback/safe-disable posture, redaction,
  CLI parity, and focused verifiers are present.

## Coding Cockpit Prompt 04 Apply Readiness

Prompt 04 keeps the full approved apply goal visible while blocking execution
until the missing contracts are implemented.

Full-strength version:

- UAA applies selected files or hunks from an exact Coding patch proposal after
  operator approval, checkpoint creation, receipt emission, and rollback proof.
- The operator can review receipts and proof detail for the apply and rollback
  posture.

Repo-safe current version:

- `GET /control-center/coding/patch-apply-readiness` exposes a backend-owned
  read-only readiness model.
- `scripts/dev/uaa_coding.py inspect-patch-apply-readiness` provides CLI
  inspection parity.
- `/coding` shows missing exact patch body, selected hunk scope, approval
  binding, checkpoint, rollback, and sensitive diff guard prerequisites.
- The route stores safe refs and bounded summaries only.

Blocked / needs authority:

- Patch body storage, selected file or hunk apply scope, Coding apply route,
  LocalApprovalAuthority binding, checkpoint creation, apply receipt, rollback
  receipt, rollback execution, sensitive diff guard, file writes, and proof
  binding remain blocked.
- Prompt 04 does not read repo files, write files, apply patches, capture
  approval grants, execute rollback, run shell/subprocess commands, mutate Git,
  call providers/models, automate browsers, write connectors, launch background
  agents, or grant production authority.

Exact promotion path:

- Run
  `docs/prompts/authority_graduation_program/generated_unblock_prompts/unblock_coding_approved_patch_apply.prompt.md`.
- Keep the blocker report current at
  `docs/control_center/authority_graduation_blockers/coding_approved_patch_apply_2026_07_04.md`.
- Promote only after exact patch artifact storage, selection scope,
  LocalApprovalAuthority validation, checkpoint and rollback contracts, safe
  receipt storage, redaction, Proof Detail binding, CLI parity, frontend tests,
  and focused verifiers are present.

Verification:

- `tests/test_coding_cockpit_read_model.py`
- `apps/control-center/src/App.test.tsx`
- `tests/test_control_center_api_routes.py`
- `tests/test_control_center_release_surface_manifest.py`
- `scripts/verify_control_center_release_surface.py`

## Contract Ref

`contract-ref:governed-code-workbench:v1`

## Proposal Requirements

Each governed Code proposal requires:

- `proposal_ref`
- `repo_scope_ref`
- `safe_diff_summary_ref`
- `validation_plan_ref`
- `validation_result_refs`
- `approval_requirement_ref`
- `expected_apply_receipt_ref`
- `expected_rollback_receipt_ref`
- `evidence_refs`
- `idempotency_key_ref`
- `blocked_state_refs`

The proposal is safe-ref metadata only. Diff bodies, patch bodies, raw file
content, local paths, logs, provider payloads, account identifiers, credential
material, and shell output are denied from durable evidence.

## Today-Spine Binding

`GET /control-center/today/summary` now exposes:

- `governed_code_workbench_contract_ref`
- `governed_code_workbench_status`
- `governed_code_workbench_proposal_ref`
- `governed_code_workbench_repo_scope_ref`
- `governed_code_workbench_safe_diff_summary_ref`
- `governed_code_workbench_validation_plan_ref`
- `governed_code_workbench_validation_result_refs`
- `governed_code_workbench_approval_requirement_ref`
- `governed_code_workbench_expected_apply_receipt_ref`
- `governed_code_workbench_expected_rollback_receipt_ref`
- `governed_code_workbench_evidence_refs`
- `governed_code_workbench_idempotency_key_ref`
- `governed_code_workbench_safe_summary`
- `governed_code_workbench_validation_plan_summary`
- `governed_code_workbench_required_ref_fields`
- `governed_code_workbench_required_blocked_refs`
- `governed_code_workbench_surface_bindings`
- `governed_code_workbench_authority_posture`
- `governed_code_workbench_blocked_state_refs`

The Code module feed now includes
`contract-ref:governed-code-workbench:v1` and remains apply-blocked.

## Surface Binding

Governed Code metadata feeds these surfaces as safe refs only:

- Today: proposal contract, repo-local scope, validation posture, and blockers.
- Code: repo-local safe diff summary contract.
- Actions: expected apply receipt refs and approval requirement refs only.
- Evidence: validation and rollback receipt refs as history.
- Memory: reviewed cross-surface memory intake proposal refs only; memory writes
  and context injection remain blocked.

## Authority Boundary

Denied states remain explicit:

- `blocked-state:no-unapproved-mutation`: no mutation without exact approval.
- `blocked-state:no-apply-execution`: no apply execution.
- `blocked-state:no-approval-grant-capture`: no approval grant capture.
- `blocked-state:no-unrestricted-shell`: no unrestricted shell.
- `blocked-state:no-shell-subprocess-execution`: no shell/subprocess execution.
- `blocked-state:no-remote-execution`: no remote execution.
- `blocked-state:no-broad-coding-agent-autonomy`: no broad coding-agent autonomy.
- `blocked-state:no-provider-sdk-call`: no provider SDK call.
- `blocked-state:no-web-fetch`: no web fetch.
- `blocked-state:no-connector-write`: no connector write.
- `blocked-state:no-diff-body-storage`: no diff body storage.
- `blocked-state:no-production-authority`: no production authority.

Required authority flags include `repo_local_scope_required: true`,
`safe_diff_summary_only: true`, `validation_required_before_apply: true`,
`approval_required_before_apply: true`, `atomic_apply_required: true`,
`rollback_receipt_required: true`, `audit_required: true`, and
`redaction_required: true`.

Denied authority flags include `apply_execution_enabled: false`,
`approval_grant_capture_enabled: false`, `direct_file_write_enabled: false`,
`unrestricted_shell_enabled: false`,
`shell_subprocess_execution_enabled: false`, `remote_execution_enabled: false`,
`broad_coding_agent_autonomy_enabled: false`,
`provider_sdk_call_enabled: false`, `web_fetch_enabled: false`,
`connector_write_enabled: false`, `diff_body_storage_enabled: false`, and
`production_authority_enabled: false`.

## Evidence History

Evidence Timeline now includes `governed_code_workbench_proposal_ref`.

The history answers stay concrete:

- Proposed: a repo-local Code proposal with safe diff summary and validation refs.
- Approved: no apply approval or grant capture is approved here.
- Happened: only safe metadata was produced; no files were changed.
- Changed: no repo, connector, shell, model, memory, or task state changed.
- Undoable: rollback receipt refs describe required undo evidence posture only.
- Stale: proposal, validation, and approval scope must be rechecked before any
  future mutation.
- Blocked: apply execution and broad authority remain blocked.

## Verification

Required proof:

- `tests/test_uaa_p1_075_governed_code_workbench.py`
- `tests/test_founder_loop_storage.py`
- `tests/test_control_center_founder_loop_api.py`
- `apps/control-center/src/App.test.tsx`
- `scripts/verify_uaa_p1_075_governed_code_workbench.py`
- `docs/schemas/governed_code_workbench.schema.json`

## Next Milestone

UAA-P1-076 Cross-Surface Memory Intake is now implemented. UAA-P1-077
Memory-To-Loop Binding is next unless hardening finds that UAA-P1-076 needs an
incremental follow-up such as UAA-P1-076.1.
