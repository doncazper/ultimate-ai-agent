# UAA-P1-075 Governed Code Workbench V1

Status: implemented as a contract, test, verifier, Today-spine, Evidence
Timeline, Control Center metadata shape, and Prompt 01 `/coding` cockpit shell
read model seed.

This milestone makes Code narrower than broad external runtimes but better governed. It adds a
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
  `GET /control-center/coding/patch-apply-readiness`,
  `GET /control-center/coding/test-command-readiness`,
  `GET /control-center/coding/git-review`,
  `GET /control-center/coding/live-preview`,
  `GET /control-center/coding/multi-agent-review`.
- CLI inspection: `scripts/dev/uaa_coding.py inspect-session`,
  `scripts/dev/uaa_coding.py inspect-context`,
  `scripts/dev/uaa_coding.py inspect-patch-proposal`,
  `scripts/dev/uaa_coding.py inspect-patch-apply-readiness`,
  `scripts/dev/uaa_coding.py inspect-test-command-readiness`,
  `scripts/dev/uaa_coding.py inspect-git-review`,
  `scripts/dev/uaa_coding.py inspect-live-preview`,
  `scripts/dev/uaa_coding.py inspect-multi-agent-review`.
- Python Agent Core owns `CodingCockpitSessionReadModel` and
  `CodingWorkspaceContextReadModel` plus the proposal-only patch read model;
  Control Center renders the read models and mock fallback only.
- The shell shows workspace/context, task timeline, diff preview, proof preview,
  agent thread, terminal preview, Git preview, test output preview, live preview,
  authority mode selector, read-only context-pack preview, proposal-only patch
  refs, blocked apply-readiness refs, approval-required validation command refs, and
  blocked Git review, live-preview, and multi-agent review refs, and blocked
  authority refs.
- Mock fallback is visibly non-authoritative and grants no workflow truth.

Blocked / needs authority:

- File writes, patch apply, shell/subprocess execution, Git mutation,
  provider/model calls, browser automation, connector writes, background coding
  agents, production authority, public beta, public release, and broad runtime
  authority remain blocked.
- Prompt 01 stores safe refs and bounded summaries only. It does not persist raw
  prompts, raw responses, raw provider payloads, local paths, shell output,
  credentials, tokens, cookies, account identifiers, or private data.

Exact AuthorityLease capability path:

- Prompt 02 implements backend-owned context-pack preview contracts and
  inspection parity from safe refs only.
- Prompt 03 adds patch proposal artifacts without apply.
- Prompt 04 adds patch apply readiness and blocker refs without apply.
- Prompt 05 now exposes approval-required RuntimeGateway validation command
  lane refs for focused pytest, repo verifier, frontend check, and repo doctor.
  The Coding Cockpit route itself still does not execute commands.
- Prompt 06 adds Git review refs and blocker refs without live Git reads or Git
  mutation.
- Prompt 07 adds live-preview refs and blocker refs without dev-server control
  or browser automation.
- Prompt 08 adds multi-agent review slot, plan, review, diff-comparison,
  disagreement, and handoff refs without provider/model calls, provider SDK
  calls, local agent execution, background dispatch, context injection, or raw
  prompt/response persistence.
- Later approved lanes add exact patch apply, expanded allowlisted test
  commands, Git review, live preview execution, provider review, local-agent
  verification, and multi-agent execution only after scoped approval binding,
  receipts, rollback/safe-disable posture, redaction, CLI parity, and focused
  verifiers are present.

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
  and verifiers are accepted.

## Coding Cockpit Prompt 05 Validation Command Readiness

Prompt 05 keeps the full allowlisted test command goal visible while mapping
the already implemented RuntimeGateway fixed-command validation lanes into the
Coding Cockpit. The Coding route is inspection only; command execution remains
behind RuntimeGateway, AuthorityLease scope, exact Action Inbox approval,
idempotency, redaction, receipts, and safe-disable posture.

Full-strength version:

- UAA runs focused allowlisted validation commands with bounded redacted output
  summaries, exit codes, receipts, and Proof Detail links.
- Arbitrary shell, installs, network commands, destructive commands, background
  processes, and broad terminal access remain outside this lane.

Repo-safe current version:

- `GET /control-center/coding/test-command-readiness` exposes a backend-owned
  read-only readiness model that points at the exact RuntimeGateway validation
  intents.
- `scripts/dev/uaa_coding.py inspect-test-command-readiness` provides CLI
  inspection parity.
- `/coding` shows focused pytest, repo verifier, frontend check, and repo
  doctor command refs plus runtime lane refs, allowlist refs, expected receipt
  refs, runtime execution route refs, and runtime CLI refs.
- The route stores safe refs and bounded summaries only. It does not store raw
  commands, raw output, exit codes, or command receipts, and it does not run
  commands directly.

Blocked / needs authority:

- Arbitrary shell, installs, network commands, destructive commands,
  background processes, broad terminal access, Git mutation, file mutation,
  provider/model calls, browser automation, connector writes, and production
  authority remain blocked.
- Prompt 05 does not run commands itself; accepted validation execution still
  has to go through `POST /api/runtime/invocations/{id}/execute` with an exact
  RuntimeGateway command intent and approval envelope.

Exact promotion path:

- The original blocker report is superseded by the RuntimeGateway-backed
  validation lane now surfaced from Python Core.
- Promote expanded command kinds only after exact command allowlist,
  LocalApprovalAuthority binding
  where required, timeout, output redaction, exit-code capture, receipt storage,
  Proof Detail binding, CLI parity, frontend tests, and verifiers are accepted.

## Coding Cockpit Prompt 06 Git Review Readiness

Prompt 06 keeps the full Git review goal visible while blocking live Git command
execution and all Git mutation until the missing Git contracts are implemented.

Full-strength version:

- UAA shows Git status, diffs, changed files, staged/unstaged posture, commit
  proposals, pull-request description proposals, and later approved stage,
  commit, push, and draft PR actions with receipts and Proof Detail links.
- Force push, merge, tag, release, production deploy, arbitrary shell, and broad
  terminal access remain outside this lane.

Repo-safe current version:

- `GET /control-center/coding/git-review` exposes a backend-owned read-only
  proposal/readiness model.
- `scripts/dev/uaa_coding.py inspect-git-review` provides CLI inspection parity.
- `/coding` shows Git status, diff, changed-file, commit proposal, and
  pull-request proposal refs plus expected receipt refs and blocker refs.
- The route stores safe refs and bounded summaries only. It does not run Git,
  store raw Git output, store raw diffs, store raw paths, create Git receipts,
  or expose commit/PR text.

Blocked / needs authority:

- Live Git status reads, live Git diff reads, changed-file extraction, raw diff
  redaction, commit message text, pull-request description text, Git receipt
  creation, Proof Detail binding, and shell/subprocess execution remain blocked.
- Prompt 06 does not stage files, commit, push, open PRs, merge, tag, release,
  run commands, mutate files, call providers/models, automate browsers, write
  connectors, or grant production authority.

Exact promotion path:

- Run
  `docs/prompts/authority_graduation_program/generated_unblock_prompts/unblock_coding_git_review.prompt.md`.
- Keep the blocker report current at
  `docs/control_center/authority_graduation_blockers/coding_git_review_2026_07_04.md`.
- Promote only after read-only Git status and diff contracts, redaction,
  receipt storage, Proof Detail binding, CLI parity, frontend tests, and
  verifiers are accepted. Any Git mutation remains a separate exact approval
  lane.

## Coding Cockpit Prompt 07 Live Preview Readiness

Prompt 07 keeps the full live preview goal visible while blocking dev-server
control, browser preview, screenshot capture, console capture, and browser
automation until the missing preview contracts are implemented.

Full-strength version:

- UAA shows local dev server status, browser preview, console errors,
  screenshot capture, visual regression proof, route checklist, and mobile and
  desktop preview evidence with Proof Detail links.
- Starting/stopping dev servers, browser interaction, form/click automation,
  downloads/uploads, and authenticated browser state remain outside this lane.

Repo-safe current version:

- `GET /control-center/coding/live-preview` exposes a backend-owned read-only
  status/readiness model.
- `scripts/dev/uaa_coding.py inspect-live-preview` provides CLI inspection
  parity.
- `/coding` shows dev-server status, preview URL, screenshot, console,
  visual-proof, route-checklist, and viewport refs plus blocker refs.
- The route stores safe refs and bounded summaries only. It does not detect or
  start dev servers, persist raw URLs, open browsers, capture screenshots, read
  console output, or create visual proof artifacts.

Blocked / needs authority:

- Dev-server status detection, preview URL persistence, browser observe,
  browser preview, screenshot artifact capture, console capture, visual
  regression comparison, receipt creation, Proof Detail binding, and
  shell/subprocess execution remain blocked.
- Prompt 07 does not start or stop dev servers, navigate browsers, automate
  clicks/forms, run commands, mutate files, mutate Git, call providers/models,
  write connectors, or grant production authority.

Exact promotion path:

- Run
  `docs/prompts/authority_graduation_program/generated_unblock_prompts/unblock_coding_live_preview.prompt.md`.
- Keep the blocker report current at
  `docs/control_center/authority_graduation_blockers/coding_live_preview_2026_07_04.md`.
- Promote only after dev-server status, URL redaction, browser observe,
  screenshot artifact, visual proof, receipt storage, Proof Detail binding, CLI
  parity, frontend tests, and verifiers are accepted.

## Coding Cockpit Prompt 08 Multi-Agent Review Readiness

Prompt 08 keeps the full multi-agent collaboration goal visible while blocking
provider/model calls, local agent execution, background dispatch, context
injection, and raw prompt/response persistence until the missing contracts are
implemented.

Full-strength version:

- UAA coordinates Codex implementer, Claude reviewer, local verifier, security
  reviewer, UX reviewer, test fixer, and merge captain workflows with
  comparable plans, reviews, diffs, disagreements, handoffs, receipts, and
  Proof Detail links.
- Autonomous dispatch, background agents, provider calls, local verifier
  execution, test fixing, merge orchestration, and any production authority
  remain outside this capability until exact AuthorityLease scope is implemented.

Repo-safe current version:

- `GET /control-center/coding/multi-agent-review` exposes a backend-owned
  read-only proposal/readiness model.
- `scripts/dev/uaa_coding.py inspect-multi-agent-review` provides CLI
  inspection parity.
- `/coding` shows Codex implementer, Claude reviewer, local verifier, security
  reviewer, UX reviewer, test fixer, and merge captain slot refs plus plan,
  review, diff-comparison, disagreement, handoff, blocker, promotion-path, and
  unblock-prompt refs.
- The route stores safe refs and bounded summaries only. It does not store raw
  prompts, raw responses, provider payloads, raw paths, or raw file content.

Blocked / needs authority:

- Provider/model calls, provider SDK calls, local agent execution, multi-agent
  dispatch, background autonomy, context injection, artifact body storage,
  receipt creation, Proof Detail binding, and shell/subprocess execution remain
  blocked.
- Prompt 08 does not call Codex, Claude, or local agents; execute reviewers;
  fix tests; dispatch background workers; inject context; write files; mutate
  Git; run commands; automate browsers; write connectors; or grant production
  authority.

Exact promotion path:

- Run
  `docs/prompts/authority_graduation_program/generated_unblock_prompts/unblock_coding_multi_agent_review.prompt.md`.
- Keep the blocker report current at
  `docs/control_center/authority_graduation_blockers/coding_multi_agent_review_2026_07_04.md`.
- Promote only after provider/local-agent review authority, artifact storage,
  redaction, LocalApprovalAuthority binding where required, receipt storage,
  Proof Detail binding, CLI parity, frontend tests, and verifiers are accepted.

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
